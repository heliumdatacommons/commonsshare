// These event bindings will work even for elements created dynamically
$(document).on('click', '.btn-unshare-resource', function () {
    var formID = $(this).closest("form").attr("id");
    unshare_resource_ajax_submit(formID);
});

$(document).on('click', '.btn-undo-share', function () {
    var formID = $(this).closest("form").attr("id");
    undo_share_ajax_submit(formID);
});

$(document).on("click", ".btn-change-share-permission", function () {
    var arg = $(this).attr("data-arg");
    change_share_permission_ajax_submit(arg);
});

$(document).ready(function() {
    var resID = $("#resID").val();

    $("#download-bag-btn").click(function() {
        $("#license-agree-dialog-bag").modal('hide');
    });

    $("#btn-add-author, #btn-add-hydroshare-user").click(function() {
        get_user_info_ajax_submit('/hsapi/_internal/get-user-or-group-data/', this)
    });

    $("#btn-confirm-extended-metadata").click(function () {
        addEditExtraMeta2Table();
    });

    $("#btn-confirm-add-access").click(function () {
        var formID = $(this).closest("form").attr("id");
        share_resource_ajax_submit(formID);
    });

});