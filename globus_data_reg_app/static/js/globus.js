$('#btn-select-globus-file').on('click',function(event) {
    $('#file_struct').children().remove();
    $('.ajax-loader').hide();
    var store = '';
    $("#globus_content_label").text(sessionStorage.IRODS_username);
    $('#root_store').val(sessionStorage.IRODS_datastore);
    store = sessionStorage.IRODS_datastore;

    // Setting up the view tab
    $('#file_struct').attr('name',store);
    $('#globus_view_store').val(store);
    // loading file structs
    var parent = $('#file_struct');
    get_store(store, parent, 0);
    $('body').off('click');
    $('body').on('click', '.folder', click_folder_opr);
});

function set_store_display(store, parent, margin, json) {
    var files = json.files;
    var folder = json.folder;
    var lastSelected = [];
    if (files.length == 0 && folder.length == 0) {
        $(parent).append("<div class='file' style='margin-left:" + margin + "px;'></div>");
    }
    else {
        $.each(folder, function(i, v) {
            $(parent).append("<div class='folder' id='globus_folder_" + v + "' name='" + store + "/" + v + "' style='margin-left:" + margin + "px;'><img src='/static/img/folder.png' width='15' height='15'>&nbsp; " + v + "</div>");
        });

        $.each(files, function(i, v) {
            $(parent).append("<div class='file' id='globus_file_" + v + "' name='" + store + "/" + v + "' style='margin-left:" + margin + "px;'><img src='/static/img/file.png' width='15' height='15'>&nbsp; " + v + "</div>")
        });
    }
    $('.file').attr('unselectable', 'on'); // disable default browser shift text selection highlighting in IE
    $('.file').on('click',function(e) {
        var current = $(this), selected;
        if (e.shiftKey) {
            if (lastSelected.length > 0) {
                if (current[0] == lastSelected[0]) {
                    return false;
                }
                if (current.nextAll('.lastSelected').length > 0) {
                    // last selected is after the current selection
                    selected = current.nextUntil(lastSelected);
                }
                else {
                    // last selected is before the current selection
                    selected = lastSelected.nextUntil(current);
                }
                $('.file').removeClass('selected');
                selected.addClass('selected');
                lastSelected.addClass('selected');
                current.addClass('selected');
            }
            else {
                lastSelected = current;
                current.addClass('lastSelected');
                $('.file').removeClass('selected');
                current.addClass('selected');
            }
        }
        else { // Not a shift select
            $('.file').removeClass('lastSelected');
            if (!e.ctrlKey) { // not a ctrl select - clear up old selections
                $('.file').removeClass('selected');
            }

            if (e.ctrlKey && $(e.target).hasClass('selected')) { // ctrl-clicking on a selected item clears the selection
                $(e.target).removeClass('selected');
            }
            else {
                $(e.target).addClass('lastSelected selected');
                lastSelected = current;
            }
        }
        set_datastore(current.parent('div')[0], false);
        return false;
    });
}

function get_store(store, parent, margin) {
    if (store) {
        $.ajax({
            mode: "queue",
            url: '/globus/store/',
            async: true,
            type: "POST",
            data: {
                store: store
            },
            success: function (json) {
                return set_store_display(store, parent, margin, json);
            },

            error: function (xhr, errmsg, err) {
                console.log(xhr.status + ": " + xhr.responseText + ". Error message: " + errmsg);
                return false;
            }
        });
        return true;
    }
    else
        return false;
}

function click_folder_opr() {
    var margin_left = parseInt($(this).css('margin-left')) + 10;
    if($(this).hasClass('isOpen')) {
        $(this).addClass('isClose');
        $(this).removeClass('isOpen');
        $(this).children('div').hide();
        set_datastore($(this).attr('name'), true);
    }
    else if($(this).hasClass('isClose')) {
        $(this).addClass('isOpen');
        $(this).removeClass('isClose');
        $(this).children('div').show();
    }
    else {
        var store = $(this).attr('name');
        var parent = $(this)
        get_store(store, parent, margin_left);
        $(this).addClass('isOpen');
        set_datastore($(this).attr('name'), true);
    }
    return false;
}

function set_datastore(store, isFolder) {
    if (store) {
        if (!isFolder) {
            store = $(store).attr('name');
        }
        $('#globus_view_store').val(store);
    }
};

$("#globusContent form").bind("keypress", function(e) {
    if (e.keyCode == 13) {
        $("#btnSearch").attr('value');
        //add more buttons here
        return false;
    }
});

function globus_register() {
    $.ajax({
        url: "/globus/register/",
        type: "POST",
        data: {
            path: $('#register_store').val()
        },
        success: function(json) {
            $("#globus-sel-file").text(json.globus_sel_file + ' is registered successfully.');
            $('#globusContent').modal('hide');
        },
        error: function(xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText + ". Error message: " + errmsg);
            $("#globus-sel-file").text("No file is registered.");
            $('#globusContent').modal('hide');
        }
    });
}

$('#globusRegister').on('submit', function(event) {
    event.preventDefault();
    globus_register();
});
