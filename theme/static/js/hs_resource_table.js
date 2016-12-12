/**
 * Created by Mauriel on 5/19/2016.
 */
var resourceTable;

var ACTIONS_COL = 0;
var RESOURCE_TYPE_COL = 1;
var TITLE_COL = 2;
var OWNER_COL = 3;
var DATE_CREATED_COL = 4;
var LAST_MODIFIED_COL = 5;
var SUBJECT_COL = 6;
var AUTHORS_COL = 7;
var PERM_LEVEL_COL = 8;
var LABELS_COL = 9;
var FAVORITE_COL = 10;
var LAST_MODIF_SORT_COL = 11;
var SHARING_STATUS_COL = 12;
var DATE_CREATED_SORT_COL = 13;
var ACCESS_GRANTOR_COL = 14;

$(document).ready(function () {
/*==================================================
    Table columns
    0 - actions
    1 - Resource Type
    2 - Title
    3 - Owner
    4 - Date Created
    5 - Last Modified
    6 - Subject
    7 - Authors
    8 - Permission Level
    9 - Labels
    10 - Favorite
    11 - Last modified (sortable format)
    12 - Sharing Status
    13 - Date created (sortable format)
    14 - Access Grantor
==================================================*/

    resourceTable = $("#item-selectors").DataTable({
        "order": [[DATE_CREATED_COL, "desc"]],
        "paging": false,
        "info": false,
        "columnDefs": colDefs
    });

    $("#item-selectors").css("width", "100%");

    // Fix for horizontal scroll bar appearing unnecessarily on firefox.
    if ($.browser.mozilla){
        $("#item-selectors").width($("#item-selectors").width() - 2);
    }

    // Trigger label creation when pressing Enter
    $("#txtLabelName").keyup(function (event) {
        var label = $("#txtLabelName").val().trim();
        if (event.keyCode == 13 && label != "") {
            $("#btn-create-label").click();
        }
    });

    // Disable default form submission when pressing enter for textarea inputs
    $(window).keydown(function (event) {
        if (event.keyCode == 13 && event.target.tagName != "TEXTAREA") {
            event.preventDefault();
        }
    });

    // Autofocus input when modal appears
    $("#modalCreateLabel").on('shown.bs.modal', function () {
        $("#txtLabelName").focus();
    });


    $("#item-selectors").show();

    // Bind ajax submit events to favorite and label buttons
    $(".btn-inline-favorite").click(label_ajax_submit);
    $(".btn-label-remove").click(label_ajax_submit);
    $("#btn-create-label").click(label_ajax_submit);

    $("#resource-search-input").keyup(function () {
        var searchString = removeQueryOccurrences($(this).val());
        applyQueryStrings();
        resourceTable.search(searchString).draw();
    });

    $("#btn-clear-author-input").click(function () {
        $("#input-author").val("");
        typeQueryStrings();
        $("#resource-search-input").keyup();
    });

    $("#btn-clear-subject-input").click(function () {
        $("#input-subject").val("");
        typeQueryStrings();
        $("#resource-search-input").keyup();
    });

    $("#btn-clear-search-input").click(function () {
        var searchInput = $("#resource-search-input");
        searchInput.val("");
        searchInput.keyup();
    });

    $('#input-author, #input-subject').keyup( function() {
        typeQueryStrings();
        resourceTable.draw();
    } );

    $("#input-resource-type").change(function(){
        typeQueryStrings();
        resourceTable.draw();
    });

    $(".all-rows-selector").change(function(){
        $(".row-selector").prop("checked", $(this).prop("checked"));

        var toolbarLabels = $("#toolbar-labels-dropdown input[type='checkbox']");
        if ($(this).prop("checked") == false) {
            toolbarLabels.attr("disabled", true);
        }
        else {
            toolbarLabels.attr("disabled", false);
        }

        refreshToolbarCheckboxState();
    });

    $(".row-selector").change(refreshToolbarCheckboxState);

    $("#btn-favorite").click(function(){
        var stars = $("#item-selectors input[type='checkbox']:checked").parent().find(".btn-inline-favorite");
        var checkedSome = false;
        for (var i = 0; i < stars.length; i++) {
            if (!$(stars[i]).hasClass("isfavorite")) {
                $(stars[i]).click();
                checkedSome = true;
            }
        }

        // If none was checked it means we are unchecking all
        if (checkedSome == false) {
            stars.click();
        }
    });

    $("#item-selectors td").click(function(e){
        if (e.target.tagName != "TD") {
            return;
        }
        if ($(this).parent().find("input[type='checkbox']:checked.row-selector").length > 0) {
            $(this).parent().find("input[type='checkbox'].row-selector").prop("checked", false);
        }
        else {
            $(this).parent().find("input[type='checkbox'].row-selector").prop("checked", true);
        }
    });

    // Prevents dropdown form getting dismissed when clicking on items
    $('.dropdown-menu label, .list-labels label').click(function (e) {
        e.stopPropagation();
    });

    updateLabelLists();
    updateLabelCount();

});

function label_ajax_submit() {
    var el = $(this);
    var form = $("form[data-id='" + el.attr("data-form-id") + "']");
    var datastring = form.serialize();
    var url = form.attr('action');
    var formType = el.attr("data-form-type");
    var tableRow = form.closest("tr");

    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        data: datastring,
        success: function (result) {
            var json_response = JSON.parse(result);
            if (json_response.status == "success") {
                if (formType == "create-label") {
                    createLabel();
                }
                else if (formType == "delete-label") {
                    var deletedLabel = el.attr("data-label");
                    $("#table-user-labels td[data-label='" + deletedLabel + "']").parent().remove();
                    if ($("#table-user-labels .user-label").length == 0 && $("#table-user-labels .no-items-found").length == 0) {
                        $("#table-user-labels tbody").append(
                                '<tr class="no-items-found"><td>No labels found.</td></tr>'
                        )
                    }
                    updateLabelLists();
                    refreshToolbarCheckboxState();
                }
                else if (formType == "toggle-favorite") {
                    var action = form.find("input[name='action']");

                    el.toggleClass("isfavorite");
                    var rowIndex = parseInt(form.closest("tr").attr("data-tr-index"));
                    var favoriteColIndex = 9;   // Index of the favorite column in the table

                    if (json_response.action == "DELETE") { // Got unchecked
                        action.val("CREATE");
                        resourceTable.cell(rowIndex,favoriteColIndex).data("").draw();
                    }
                    else {                          // Got checked
                        action.val("DELETE");

                        resourceTable.cell(rowIndex,favoriteColIndex).data("Favorite").draw();  // .draw refreshed the internal cache of the table object
                    }
                }
                else if (formType = "toggle-label") {
                    var action = form.find("input[name='action']");
                    var label = el[0].value;

                    var rowIndex = parseInt(tableRow.attr("data-tr-index"));
                    var currentCell = resourceTable.cell(rowIndex,LABELS_COL);

                    var dataColLabels = currentCell.data().replace(/\s+/g,' ').split(","); // List of labels already applied to the resource;

                    // Remove extra spaces from the labels collection
                    for (var i = 0; i < dataColLabels.length; i++) {
                        dataColLabels[i] = dataColLabels[i].trim();
                    }

                    if (json_response.action == "DELETE") { // Label got unchecked
                        action.val("CREATE");
                        var labelIndex = dataColLabels.indexOf(label);
                        dataColLabels.splice(labelIndex, 1);    // Remove label
                        currentCell.data(dataColLabels.join()).draw();
                    }
                    else {
                        action.val("DELETE");       // Label got checked
                        dataColLabels.push(label);
                        currentCell.data(dataColLabels.join()).draw();
                    }

                    // If the row has labels, color the label icon blue
                    var labelButton = $("#item-selectors tr[data-tr-index='" + rowIndex + "']").find(".btn-inline-label");
                    if (dataColLabels.length > 0) {
                        if (dataColLabels.length == 1 && dataColLabels[0].trim() == "") {   // The list could have an empty []
                            labelButton.removeClass("has-labels");
                        }
                        else {
                            labelButton.addClass("has-labels");
                        }
                    }
                    else {
                        labelButton.removeClass("has-labels");
                    }
                }

                updateLabelCount();
                refreshToolbarCheckboxState();
            }

        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {

        }
    });

    //don't submit the form
    return false;
}

function updateLabelLists() {
    $("#user-labels-left").empty();
    $(".inline-dropdown ul").empty();
    $("#toolbar-labels-dropdown ul :not(.persist)").empty();
    $(".btn-inline-label").removeClass("has-labels");

    var labels = $("#table-user-labels td.user-label");
    for (var h = 0; h < labels.length; h++) {
        var curr = $(labels[h]).text();

        $("#user-labels-left").append(
                '<li class="list-group-item">' +
                '<span class="badge">0</span>' +
                '<label class="checkbox">' +
                '<input data-label="' + curr + '" type="checkbox">' + curr + '</label>' +
                '</li>'
        );

        var dropdowns = $(".inline-dropdown ul");

        if (dropdowns) {
            for (var i = 0; i < dropdowns.length; i++) {
                var res_id = $(dropdowns[i]).attr("data-resource-id");
                var formID = "form-" + i + "-" + h + "-" + res_id;
                $(dropdowns[i]).append(
                        '<li>' +
                        '<label class="checkbox"><input data-form-type="toggle-label" data-form-id="' + formID + '" type="checkbox" value="' + curr + '">' + curr + '</label>' +
                        '<form data-id="' + formID + '" class="hidden-form" action="/hsapi/_internal/' + res_id + '/label-resource-action/"' +
                        'method="post">' +
                        document.getElementById("csrf").innerHTML +
                        '<input type="hidden" name="label" value="' + curr + '">' +
                        '<input type="hidden" name="label_type" value="LABEL">' +
                        '<input type="hidden" name="action" value="CREATE">' +
                        '</form>' +
                        '</li>'
                );
            }
        }


        if ($(".row-selector:checked").length == 0) {
            $("#toolbar-labels-dropdown ul").prepend(
                    '<li>' +
                    '<label class="checkbox"><input disabled type="checkbox" value="' + curr + '">' + curr + '</label>' +
                    '</li>'
            );
        }
        else {

            $("#toolbar-labels-dropdown ul").prepend(
                    '<li>' +
                    '<label class="checkbox"><input type="checkbox" value="' + curr + '">' + curr + '</label>' +
                    '</li>'
            );
        }

        // $(".inline-dropdown input[type='checkbox']").change(updateLabelCount);
    }

    // Check checkboxes for labels currently in the resource
    if (dropdowns) {
        for (var i = 0; i < dropdowns.length; i++) {
            var rowIndex = parseInt($(dropdowns[i]).closest("tr").attr("data-tr-index"));

            var dataColLabels = resourceTable.cell(rowIndex,LABELS_COL).data().replace(/\s+/g,' ').split(",");

            for (var j = 0; j < dataColLabels.length; j++) {
                var label = dataColLabels[j].trim();
                var currentCheckbox = $(dropdowns[i]).find("input[type='checkbox'][value='" + label + "']");
                currentCheckbox.prop("checked", true);
                currentCheckbox.closest("li").find("form input[name='action']").val("DELETE");
            }

            if (dataColLabels.length > 0) {
                if (dataColLabels.length == 1 && dataColLabels[0].trim() == "") {
                    $(dropdowns[i]).closest("tr").find(".btn-inline-label").removeClass("has-labels");
                }
                else {
                    $(dropdowns[i]).closest("tr").find(".btn-inline-label").addClass("has-labels");
                }
            }
        }
    }

    if (labels.length == 0) {
        $("#user-labels-left").append(
                '<i class="list-group-item no-items-found"><h5>No labels found.</h5></i>'
        );

        $("#toolbar-labels-dropdown ul").prepend(
                 '<i class="no-items-found list-group-item"><h5>No labels found.</h5></i>'
        );

        $(".btn-inline-label").attr("data-toggle", "");
    }
    else {
        $(".btn-inline-label").attr("data-toggle", "dropdown");
    }

    // -----------------   Bind events   -----------------
    $("#filter input[type='checkbox']").change(function(){
        resourceTable.draw();
    });

    $("#filter-shared-by input[type='checkbox']").change(function(){
        resourceTable.draw();
    });

    $("#user-labels-left input[type='checkbox']").change(function () {
        resourceTable.draw();
    });

    $(".inline-dropdown input[type='checkbox']").change(label_ajax_submit);

    $("#toolbar-labels-dropdown input[type='checkbox']").change(function(){
        var inlineCheckboxes = $(".row-selector:checked").parent().find(".inline-dropdown input[type='checkbox'][value='" + $(this).val() + "']");
        var status = $(this).prop("checked");

        for (var i = 0; i < inlineCheckboxes.length; i++) {
            if (status == false && $(inlineCheckboxes[i]).prop("checked") == true) {
                $(inlineCheckboxes[i]).prop("checked", false);
                $(inlineCheckboxes[i]).trigger("change");
            }
            else if (status == true && $(inlineCheckboxes[i]).prop("checked") == false) {
                $(inlineCheckboxes[i]).prop("checked", true);
                $(inlineCheckboxes[i]).trigger("change");
            }
        }
    });

    // Prevents dropdown form getting dismissed when clicking on items
    $('.dropdown-menu label, .list-labels label').click(function (e) {
        e.stopPropagation();
    });
}

// Checks and unchecks label checkbox in the toolbar depending on which table rows are selected.
function refreshToolbarCheckboxState() {
    var toolbarLabels = $("#toolbar-labels-dropdown input[type='checkbox']");
    var selectedRows = $(".row-selector:checked");
    if (selectedRows.length == 0) {
        toolbarLabels.attr("disabled", true);
        return;
    }

    toolbarLabels.attr("disabled", false);
    toolbarLabels.prop("checked", true);

    var inlineCheckboxes = selectedRows.parent().find(".inline-dropdown input[type='checkbox']:not(:checked)");

    // Uncheck label checkbox in toolbar
    for (var i = 0; i < inlineCheckboxes.length; i++) {
        var label = $(inlineCheckboxes[i]).val();
        $("#toolbar-labels-dropdown .list-labels input[type='checkbox'][value='" + label + "']").prop("checked", false);
    }
}

function createLabel () {
    if ($("#txtLabelName").val() != "") {
        var userLabelsTable = $("#table-user-labels tbody");
        userLabelsTable.append(
                '<tr>' +
                    '<td class="user-label" data-label="' + $("#txtLabelName").val() + '">' + $("#txtLabelName").val() + '</td>' +
                    '<td>'+
                        '<form class="hidden-form" data-id="form-delete-label-'+ $("#txtLabelName").val() + '" ' +
                              'action="/hsapi/_internal/label-resource-action/"'+
                              'method="post">'+
                            document.getElementById("csrf").innerHTML +
                            '<input type="hidden" name="label" value="' + $("#txtLabelName").val() + '">'+
                            '<input type="hidden" name="label_type" value="SAVEDLABEL">'+
                            '<input type="hidden" name="action" value="DELETE">'+
                        '</form>'+
                        '<span data-label="' + $("#txtLabelName").val() + '" data-form-type="delete-label"'+
                              'class="btn-label-remove glyphicon glyphicon-remove"'+
                              'data-form-id="form-delete-label-' + $("#txtLabelName").val() + '"></span>'+
                    '</td>'+
                '</tr>');

        userLabelsTable.find(".no-items-found").remove();

        $(".btn-label-remove").click(label_ajax_submit);
        $("#modalCreateLabel").modal('hide');
         $("#txtLabelName").val("");
        updateLabelLists();
    }
}

function updateLabelCount() {
    $("#labels input[data-label]").parent().parent().find(".badge").text("0");
    $("#toolbar-labels-dropdown input[type='checkbox']").prop("checked", true);

    var collection = [];
    var favorites = 0;
    var ownedCount = 0;
    var ownedEditableCount = 0;
    var editableCount = 0;
    var viewableCount = 0;

    resourceTable.rows().every(function(rowIndex, tableLoop, rowLoop) {
        var dataColLabels = this.data()[LABELS_COL].replace(/\s+/g, ' ').split(","); // List of labels already applied to the resource;
        var dataColFavorite = this.data()[FAVORITE_COL].trim();
        var dataColPermissionLevel = this.data()[PERM_LEVEL_COL].trim();
        var sharingStatus = this.data()[SHARING_STATUS_COL].trim();

        if (dataColPermissionLevel == "Owned") {
            ownedCount++;
            if (sharingStatus.indexOf('Published') == -1)
                ownedEditableCount++;
        }
        else if (dataColPermissionLevel == "Editable") {
            editableCount++;
        }
        else if (dataColPermissionLevel == "Viewable") {
            viewableCount++;
        }

        // Update filter badges count
        $("#filter .badge[data-facet='owned']").text(ownedCount);
        $("#filter .badge[data-facet='editable']").text(ownedEditableCount+editableCount);
        $("#filter .badge[data-facet='viewable by me']").text(viewableCount+editableCount+ownedCount);

        if (dataColFavorite == "Favorite") {
            favorites++;
        }

        // Loop through the labels in the row and update the collection count
        for (var i = 0; i < dataColLabels.length; i++) {
            var label = dataColLabels[i].trim();
            if (!collection[label]) {
                collection[label] = 0;
            }
            collection[label]++;
        }
    });

    // Set label counts
    for (var key in collection) {
        $("#labels input[data-label='" + key + "']").parent().parent().find(".badge").text(collection[key]);
    }

    // Set favorite count
    $("#filter .badge[data-facet='favorites']").text(favorites);
}

//strips query inputs from a search string
function removeQueryOccurrences(inputString) {
    // Matches occurrences of query strings. i.e.: "[author:mauriel ramirez]", "[]", etc
    var regExp = /\[([^\]|^\[]?)+\]/g;
    var occurrences = inputString.match(regExp);

    if (occurrences) {
        // Remove query occurrences from input string
        for (var i = 0; i < occurrences.length; i++) {
            inputString = inputString.replace(occurrences[i], "");
        }
    }

    return inputString;
}

// Looks at the query strings in the searchbox and sets the values in the dropdown options
function applyQueryStrings() {
    var inputString = $("#resource-search-input").val().toLowerCase();
    // Matches occurrences of query strings. i.e.: author:mauriel
    var regExp = /\[(type|author|subject):[^\]|^\[]+]/g;
    var occurrences = inputString.match(regExp);

    var inputType = "";
    var inputSubject = "";
    var inputAuthor = "";

    var collection = [];
    if (occurrences) {
        for (var item in occurrences) {
            var content = occurrences[item].replace("[", "").replace("]", "").split(":");
            collection.push(content);
        }
    }

    for (var item in collection) {
        if (collection[item][0].toUpperCase() == "TYPE") {
            inputType = collection[item][1];
        }
        else if (collection[item][0].toUpperCase() == "AUTHOR") {
            inputAuthor = collection[item][1];
        }
        else if (collection[item][0].toUpperCase() == "SUBJECT") {
            inputSubject = collection[item][1];
        }
    }

    $("#input-author").val(inputAuthor);
    $("#input-subject").val(inputSubject);
    $("#input-resource-type").val(inputType.toLowerCase());

}

// Looks at the values in the dropdown options and appends the corresponding query string to the search box.
function typeQueryStrings () {
    var searchInput = $("#resource-search-input");

    var type = $("#input-resource-type").val();
    var author = $("#input-author").val();
    var subject = $("#input-subject").val();

    var searchQuery = "";

    if (type) {
        searchQuery = searchQuery + " [type:" + type + "]";
    }

    if (author) {
        searchQuery = searchQuery + " [author:" + author + "]";
    }

    if (subject){
        searchQuery = searchQuery + " [subject:" + subject + "]";
    }

    searchQuery = searchQuery + removeQueryOccurrences(searchInput.val());
    searchQuery = searchQuery.trim();
    searchInput.val(searchQuery);
}


/*==================================================
    Table columns
    0 - actions
    1 - Resource Type
    2 - Title
    3 - Owner
    4 - Date Created
    5 - Last Modified
    6 - Subject
    7 - Authors
    8 - Permission Level
    9 - Labels
    10 - Favorite
    11 - Last modified (sortable format)
    12 - Sharing Status
    13 - Date created (sortable format)
    14 - Access Grantor
==================================================*/

/* Custom filtering function which will search data for the values in the custom filter dropdown or query strings */
$.fn.dataTable.ext.search.push (
        function (settings, data, dataIndex) {
            var inputString = $("#resource-search-input").val().toLowerCase();
            // Matches occurrences of query strings. i.e.: author:mauriel
            var regExp = /\[(type|author|subject):[^\]|^\[]+]/g;
            var occurrences = inputString.match(regExp);

            var inputType = "";
            var inputSubject = "";
            var inputAuthor = "";

            // Split the occurrences at ':' and move to an array.
            var collection = [];
            if (occurrences) {
                for (var item in occurrences) {
                    var content = occurrences[item].replace("[", "").replace("]", "").split(":");
                    collection.push(content);
                }
            }

            // Extract the pieces of information
            for (var item in collection) {
                if (collection[item][0].toUpperCase() == "TYPE") {
                    inputType = collection[item][1];
                }
                else if (collection[item][0].toUpperCase() == "AUTHOR") {
                    inputAuthor = collection[item][1];
                }
                else if (collection[item][0].toUpperCase() == "SUBJECT") {
                    inputSubject = collection[item][1];
                }
            }

            // Filter the table for each value

            if (inputType && data[RESOURCE_TYPE_COL].toUpperCase().indexOf(inputType.toUpperCase()) == -1) {
                return false;
            }

            if (inputSubject && data[SUBJECT_COL].toUpperCase().indexOf(inputSubject.toUpperCase()) == -1) {
                return false;
            }

            if (inputAuthor && data[AUTHORS_COL].toUpperCase().indexOf(inputAuthor.toUpperCase()) == -1) {
                return false;
            }

            //---------------- Facets filter--------------------
            // Owned by me
            if ($('#filter input[type="checkbox"][value="Owned"]').prop("checked") == true) {
                if (data[PERM_LEVEL_COL] != "Owned") {
                    return false;
                }
            }

            // Editable by me
            if ($('#filter input[type="checkbox"][value="Editable"]').prop("checked") == true) {
                // published resources are not editable
                var sharingStatus = data[SHARING_STATUS_COL].trim();
                if (sharingStatus.indexOf('Published') != -1)
                    return false;

                if (data[PERM_LEVEL_COL] != "Owned" && data[PERM_LEVEL_COL] != "Editable") {
                    return false;
                }
            }

            // Viewable by me
            if ($('#filter input[type="checkbox"][value="View"]').prop("checked") == true) {
                // published resources are viewable
                var sharingStatus = data[SHARING_STATUS_COL].trim();
                if (sharingStatus.indexOf('Published') != -1)
                    return true;

                if (data[PERM_LEVEL_COL] != "Owned" && data[PERM_LEVEL_COL] != "Viewable" && data[PERM_LEVEL_COL] != "Editable") {
                    return false;
                }
            }

            // Shared by - Used in group resource listing
            var grantors = $('#filter-shared-by .grantor:checked');
            if (grantors.length) {
                var grantorFlag = false;
                for (var i = 0; i < grantors.length; i++) {
                    var user = parseInt($(grantors[i]).attr("data-grantor-id"));
                    if (parseInt(data[ACCESS_GRANTOR_COL]) == user) {
                        grantorFlag = true;
                    }
                }

                if (!grantorFlag) {
                    return false;
                }
            }

            // Labels - Check if the label exists in the table
            var labelCheckboxes = $("#user-labels-left input[type='checkbox']");
            for (var i = 0; i < labelCheckboxes.length; i++) {
                if ($(labelCheckboxes[i]).prop("checked") == true) {
                    var label = $(labelCheckboxes[i]).attr("data-label");

                    var dataColLabels = data[LABELS_COL].replace(/\s+/g,' ').split(",");
                    for (var h = 0; h < dataColLabels.length; h++) {
                        dataColLabels[h] = dataColLabels[h].trim();
                    }

                    if (dataColLabels.indexOf(label) == -1) {
                        return false;
                    }
                }
            }

            // Favorite
            if ($('#filter input[type="checkbox"][value="Favorites"]').prop("checked") == true) {
                if (data[FAVORITE_COL] != "Favorite") {
                    return false;
                }
            }

            // Default
            return true;
        }
);