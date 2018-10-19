var markers = [];
var raw_results = [];

var updateListView = function (data) {
    var requestURL = "/search/";

    if (window.location.search.length == 0) {
        requestURL += "?q=";
    } else {
        var textSearch = $("#id_q").val();
        var searchURL = "?q=" + textSearch;
        requestURL += searchURL;
        requestURL += buildURLOnCheckboxes();
    }
    $("#discover-list-loading-spinner").show();
    $.ajax({
        type: "GET",
        url: requestURL,
        data: data,
        dataType: 'html',
        success: function (data) {
            $('#items-discovered_wrapper').empty();
            $("#discover-page-options").empty();
            var tableDiv = $("#items-discovered", data);
            $("#items-discovered_wrapper").html(tableDiv);
            var pageOptionDiv = $("#discover-page-options", data);
            $("#discover-page-options").html(pageOptionDiv);

            initializeTable();
            $("#discover-list-loading-spinner").hide();
        },
        failure: function (data) {
            console.error("Ajax call for updating list-view data failed");
            $("#discover-list-loading-spinner").hide();
        }
    });
};

var updateFacetingItems = function (request_url) {
    $("#discover-list-loading-spinner").show();

    $.when(updateListFaceting(request_url)).done(function(){
        $("#discover-list-loading-spinner").hide();
    });

};

var updateListFaceting = function (request_url) {
    return $.ajax({
        type: "GET",
        url: request_url,
        dataType: 'html',
        success: function (data) {
            $('#items-discovered_wrapper').empty();
            $("#discover-page-options").empty();
            var tableDiv = $("#items-discovered", data);
            $("#items-discovered_wrapper").html(tableDiv);
            var pageOptionDiv = $("#discover-page-options", data);
            $("#discover-page-options").html(pageOptionDiv);
            initializeTable();
        },
        failure: function (data) {
            console.error("Ajax call for updating list-view data failed");
        }
    });
};

var reorderDivs = function() {
    var faceted_fields = ['creators', 'subjects', 'resource_type', 'owners_names',
        'availability'];
    var div_ordering = [];
    faceted_fields.forEach(function(field) {
        var faceting_div = "faceting-"+field;
        div_ordering.push(faceting_div);
    });
    var i;
    for (i = 1; i < div_ordering.length; i++) {
        var div0 = "#" + div_ordering[i-1];
        var div1 = "#" + div_ordering[i];
        $(div1).insertAfter(div0);
    }
};

var formOrderParameters = function() {
    var sort_order = $("#id_sort_order").val();
    var sort_direction = $("#id_sort_direction").val();
    return "&sort_order="+sort_order+"&sort_direction="+sort_direction;
};

var buildURLOnCheckboxes = function () {
    var requestURL = '';
    $(".faceted-selections").each(function () {
        var checkboxId = $(this).attr("id");
        var sessionStorageCheckboxId = 'search-' + checkboxId;
        if(document.getElementById(checkboxId).checked){
            var arr = $(this).val().split(",");
            var key = arr[0];
            var value = arr[1];
            requestURL += "&selected_facets="+key+"_exact:"+value;
        }
    });
    return requestURL;
};

var popCheckboxes = function() {
    $(".faceted-selections").each(function () {
        var checkboxId = $(this).attr("id");
        var sessionStorageCheckboxId = 'search-' + checkboxId;
        var val = sessionStorage[sessionStorageCheckboxId];
        var isChecked = val !== undefined ? val == 'true' : false;
        $(this).prop("checked", isChecked);
    });
};

var clearCheckboxes = function() {
    $(".faceted-selections").each(function () {
        var checkboxId = $(this).attr("id");
        var sessionStorageCheckboxId = 'search-' + checkboxId;
        sessionStorage[sessionStorageCheckboxId] = 'false';
        sessionStorage.removeItem(sessionStorageCheckboxId);
    });
};

var clearAllFaceted = function() {
    clearCheckboxes();
    var clearURL = "/search/";
    window.location = clearURL;
};

function initializeTable() {
    var RESOURCE_TYPE_COL = 0;
    var TITLE_COL = 1;
    var OWNER_COL = 2;
    var DATE_CREATED_COL = 3;
    var DATE_CREATED_SORT_COL = 4;
    var LAST_MODIFIED_COL = 5;
    var LAST_MODIF_SORT_COL = 6;

    var colDefs = [
        {
            "targets": [RESOURCE_TYPE_COL],     // Resource type
            "width": "110px"
        },
        {
            "targets": [DATE_CREATED_COL],     // Date created
            "iDataSort": DATE_CREATED_SORT_COL
        },
        {
            "targets": [LAST_MODIFIED_COL],     // Last modified
            "iDataSort": LAST_MODIF_SORT_COL
        },
        {
            "targets": [LAST_MODIF_SORT_COL],     // Last modified (for sorting)
            "visible": false
        },
        {
            "targets": [DATE_CREATED_SORT_COL],     // Last modified (for sorting)
            "visible": false
        }
    ];

    $('#items-discovered').DataTable({
        "paging": false,
        "searching": false,
        "info": false,
        "ordering": false,
        // "order": [[TITLE_COL, "asc"]],
        "columnDefs": colDefs
    });
}

$(document).ready(function () {
    $("#id_start_date").datepicker({
        dateFormat: 'mm/dd/yy',
        changeMonth: true,
        changeYear: true,
        yearRange: '1950:'
    });
    $("#id_end_date").datepicker({
        dateFormat: 'mm/dd/yy',
        changeMonth: true,
        changeYear: true,
        yearRange: '1950:'
    });

    if (window.location.search.length == 0) {
        clearCheckboxes();
    }
    $(".search-field").keypress(function(event) {
        if (event.which == 13) {
            event.preventDefault();
            clearCheckboxes();
            var textSearch = $("#id_q").val();
            var searchURL = "?q=" + textSearch;
            var sortOrderParams = formOrderParameters();
            var windowPath = window.location.pathname;
            var requestURL =  windowPath + searchURL + sortOrderParams;
            window.location = requestURL;
        }
    });

    $("#covereage-search-fields input, #date-search-fields input, #id_q").addClass("form-control");
    $("#search-order-fields select").addClass("form-control");

    $("title").text("Discover | CommonsShare");   // Set browser tab title

    initializeTable();
    popCheckboxes();

    $("ul.nav-tabs > li > a").on("shown.bs.tab", function (e) {
        var tabId = $(e.target).attr("href").substr(1);
        window.location.hash = tabId;
    });

    $(".nav-tabs a").click(function() {
        $(this).tab('show');
    });

    // on load of the page: switch to the currently selected tab
    var hash = window.location.hash;
    $('#switch-view a[href="' + hash + '"]').tab('show');

    $("#id_q").attr('placeholder', 'Search All Public and Discoverable Resources');
    reorderDivs();

    $('.collapse').on('shown.bs.collapse', function() {
        $(this).parent().find(".glyphicon-plus").removeClass("glyphicon-plus").addClass("glyphicon-minus");
    }).on('hidden.bs.collapse', function() {
        $(this).parent().find(".glyphicon-minus").removeClass("glyphicon-minus").addClass("glyphicon-plus");
    });

    function updateResults () {
        var textSearch = $("#id_q").val();
        var searchURL = "?q=" + textSearch;
        searchURL += buildURLOnCheckboxes();
        var sortOrderParams = formOrderParameters();
        var windowPath = window.location.pathname;
        var requestURL = windowPath + searchURL + sortOrderParams;
        if (window.location.hash) {
            requestURL = requestURL + window.location.hash;
        }
        window.location = requestURL;
    }

    $("#date-search-fields input").change(function () { 
        updateResults(); 
    });

    $("#search-order-fields select").change(function () {
        updateResults(); 
    })

    $(".faceted-selections").click(function () {
        var textSearch = $("#id_q").val();
        var searchURL = "?q=" + textSearch;
        var sortOrderParams = formOrderParameters();
        var windowPath = window.location.pathname;
        var requestURL =  windowPath + searchURL;
        if($(this).is(":checked")) {
            requestURL += buildURLOnCheckboxes();
            var checkboxId = $(this).attr("id");
            var sessionStorageCheckboxId = 'search-' + checkboxId;
            sessionStorage[sessionStorageCheckboxId] = 'true';
            requestURL = requestURL + sortOrderParams;
            updateFacetingItems(requestURL);
        }
        else {
            var checkboxId = $(this).attr("id");
            var sessionStorageCheckboxId = 'search-' + checkboxId;
            sessionStorage.removeItem(sessionStorageCheckboxId);
            var updateURL =  windowPath + searchURL + buildURLOnCheckboxes() + sortOrderParams;
            updateFacetingItems(updateURL);
        }
    });

    // $("#solr-help-info").popover({
    //     html: true,
    //     container: '#body',
    //     content: '<p>Search here to find all public and discoverable resources. This search box supports <a href="https://cwiki.apache.org/confluence/display/solr/Searching" target="_blank">SOLR Query syntax</a>.</p>',
    //     trigger: 'click'
    // });

    $("#btn-show-all").click(clearAllFaceted);

});

