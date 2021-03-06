/**
* Created by Mauriel on 3/9/2017.
*/

// Preview profile picture
function readURL(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function (e) {
            var profilePicContainer = $("#profile-pic-container");
            profilePicContainer.empty();
            profilePicContainer.append(
                '<div style="background-image: url(\'' + e.target.result +  '\')"' +
                     'class="profile-pic round-image">' +
                '</div>'
            );
        };

        reader.readAsDataURL(input.files[0]);
    }
}

function validateForm() {
    var flagRequiredElements = validateRequiredElements();
    var flagEmail = validateEmail();

    return  flagRequiredElements && flagEmail;
}

function validateRequiredElements() {
    var requiredElements = $(".form-required");
    for (var i = 0; i < requiredElements.length; i++) {
        if (!$(requiredElements[i]).val()) {
            $(requiredElements[i]).addClass("form-invalid");
            $(requiredElements[i]).parent().find(".error-label").remove();
            $(requiredElements[i]).parent().append(errorLabel("This field is required."));
            return false;
        }
    }

    return true;
}

function validateEmail() {
    var regex = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;
    var email = $("#id_email");

    if (!email.val()) {
        return false;
    }

    if (!regex.test(email.val())) {
        email.parent().find(".error-label").remove();
        email.parent().append(errorLabel("Not a valid email address."));
        return false;
    }

    return true;
}

function errorLabel(message) {
    return "<div class='error-label'><div class='label label-danger'>" + message + "</div></div>";
}


function setEditMode() {
    $("[data-page-mode='view']").hide();
    $("[data-page-mode='edit']").fadeIn();
    $("[data-page-mode='on-edit-blur']").fadeTo("fast", 0.5, function () {
        $(this).addClass("blured-out");
    });

    var userTypeValue = $("#db-user-type").text();
    var selectedUserType = $('#selectUserType option[value="' + userTypeValue + '"]');

    if (selectedUserType.length > 0) {
        selectedUserType.attr('selected', 'selected');
    }
    else if (userTypeValue) {
        $('#selectUserType option[value="' + 'Other' + '"]').attr('selected', 'selected');
        $("#user-type-other").show();
        $("#selectUserType").removeAttr("name");
        var userTypeOther =  $("#user-type-other input");
        userTypeOther.attr("name", "user_type");
        userTypeOther.val(userTypeValue);
        userTypeOther.addClass("form-required");
    }

    $(".form-required").change(onFormRequiredChange);
    $("#id_email").change(validateEmail);

    // Switch to overview tab
    $('.nav-tabs a[href="#overview"]').tab('show'); // Select first tab
}

function setViewMode() {
    $("[data-page-mode='edit']").hide();
    $("[data-page-mode='view']").fadeIn();
    $("[data-page-mode='on-edit-blur']").fadeTo("fast", 1, function () {
        $(this).removeClass("blured-out");
    });
}

$(document).on('change', '#cv-custom-upload :file', function () {
    var input = $(this);
    var numFiles = input.get(0).files ? input.get(0).files.length : 1;
    var label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
    input.trigger('fileselect', [numFiles, label]);
});

function onFormRequiredChange() {
    if ($(this).val()) {
        $(this).removeClass("form-invalid");
        $(this).parent().find(".error-label").remove();
    }
    else {
        $(this).addClass("form-invalid");
        $(this).parent().find(".error-label").remove();
        $(this).parent().append(errorLabel("This field is required."));
    }
}

function irods_account_link(data_target, text) {
    return "<a data-toggle='modal' data-target='" + data_target + "'>" + text + "</a>";
}

function irods_status_info(alert_type, status, title) {
    return "<div class=\"col-sm-12\">" +
            "<div class=\"alert " + alert_type + " alert-dismissible\" role=\"alert\">" +
            "<button type=\"button\" class=\"close\" data-dismiss=\"alert\" aria-label=\"Close\"><span aria-hidden=\"true\">&times;</span></button>" +
            "<strong>" + title + "</strong><div>" + status + "</div></div></div>"
}


$(document).ready(function () {
    $('#gen_new_token').on('click', function(event) {
        $.ajax({
            mode: "queue",
            url: '/generate_token/' + $('#uid').val(),
            async: true,
            type: "POST",
            data: {
                'label': $('#token_lbl').val()
            },
            success: function (response) {
                if (response.result.length === 0)
                    $('#new_token_message').text('Failed to generate a new token');
                else {
                    $('#new_token_content').html('The generated new token: <code>' + response.result + '</code>');
                    $('#new_token_label').html('This token is labeled as : <code>' + response.label + '</code>');
                    $('#new_token_message').html('<strong>Please record the access token to use for user authentication to access API or iRODS</strong>');
                }
            },
            error: function(xhr, errmsg, err) {
                console.log(xhr.status + ": " + xhr.responseText + ". Error message: " + errmsg);
                $('#new_token_message').text('Failed to generate a new token: ' + xhr.responseText);
            }
        });
        //don't submit the form
        //return false;
    });

    $('#show_all_tokens').on('click', function(event) {
        $.ajax({
            mode: "queue",
            url: '/get_all_tokens/' + $('#uid').val(),
            async: true,
            type: "GET",
            success: function (response) {
                $('#token_list').empty();
                if (response.results.length === 0)
                    $('#token_no_result').show();
                else {
                    $('#token_no_result').hide();
                    response.results.forEach(function (result) {
                        $("#token_list").append(
                          "<option value='" + result.id + "' title='hashed token: " + result.hash + "'>" + result.label + " created at " + result.creation_time + "</option>");
                    });
                }
            },
            error: function(xhr, errmsg, err) {
                $('#token_list').empty();
                console.log(xhr.status + ": " + xhr.responseText + ". Error message: " + errmsg);
                $('#token_no_result').show();
            }
        });
    });

    $('#revoke_token').on('click', function(event) {
        //var list = document.getElementById('token_list');
        //var index = list.selectedIndex;
        //if (index < 0)
        //    $('#revoke_token_message').text('Select a token to revoke');
        //else
        //    $('#revoke_token_message').text(list[index].value + ' token is revoked successfully');
        var token_list = [] ;
        $('#token_list option:selected').each(function() {
            token_list.push({key: $(this).val(), value: $(this).text()});
        });
        if (token_list.length === 0) {
            $('#revoke_token_message').text('Select tokens to revoke');
        }
        else {
            // do an ajax call here to revoke tokens
            $.ajax({
                mode: "queue",
                url: '/delete_all_tokens/' + $('#uid').val(),
                async: true,
                type: "POST",
                data: {'tokens': JSON.stringify(token_list)},
                success: function (response) {
                    $('#revoke_token_message').text(response.message);
                },
                error: function (xhr, errmsg, err) {
                    console.log(xhr.status + ": " + xhr.responseText + ". Error message: " + errmsg);
                    var msgstr = 'Server error:' + xhr.responseText;
                    $('#revoke_token_message').text(msgstr);
                }
            });
        }
        //don't submit the form
        return false;
    });

    // Change country first empty option to 'Unspecified'
    var option = $("select[name='country'] option:first-child");
    option.val("Unspecified");
    option.text("Unspecified");

    // TODO: TESTING

    // File name preview for Add CV
    $('.btn-primary.btn-file :file').on('fileselect', function (event, numFiles, label) {
        var input = $(this).parents('.input-group').find(':text');
        input.val(label);
    });

    // Empty password input. Necessary because some browsers (ex:Firefox) now ignore 'autocomplete=off'
    setTimeout(function () {
        $("input[type=password]").val('');
    }, 500);

    $(".upload-picture").change(function(){
        readURL(this);
    });

    $("#selectUserType").change(function () {
         var inputOther = $("#user-type-other input");
        if ($(this).val() == "Other") {
            $("#user-type-other").show();
            $("#selectUserType").removeAttr("name");
            inputOther.attr("name", "user_type");
            inputOther.addClass("form-required");
            inputOther.change(onFormRequiredChange);
        }
        else {
            $("#user-type-other").hide();
            inputOther.removeAttr("name");
            inputOther.removeClass("form-required");
            $("#selectUserType").attr("name", "user_type");
        }
    });

    globus_ep_val = $("#globus-endpoints").val();
    if (globus_ep_val && globus_ep_val.length > 0)
        $("[data-page-mode='view']").hide();
    else
        $("[data-page-mode='edit']").hide();

    $("#btn-edit-profile").click(function () {
        setEditMode();
    });

    $("#btn-cancel-profile-edit").click(function () {
        setViewMode();
    });

    // Abstract collapse toggle
    $(".show-more-btn").click(function () {
        if ($(this).parent().find(".activity-description").css("max-height") == "50px") {
            var block = $(this).parent().find(".activity-description");

            block.css("max-height", "initial"); // Set max-height to initial temporarily.
            var maxHeight = block.height();    // Save the max height
            block.css("max-height", "50px");    // Restore

            block.animate({'max-height': maxHeight}, 300); // Animate to max height
            $(this).text("▲");
            $(this).attr("title", "Show less");
        }
        else {
            $(this).parent().find(".activity-description").animate({'max-height': "50px"}, 300);
            $(this).attr("title", "Show more");
            $(this).text("···");
        }
    });

    // Filter list listener
    $(".table-user-contributions tbody > tr").click(function () {
        $(".table-user-contributions tbody > tr").removeClass("active");
        $(this).addClass("active");
        var res_type = $(this).attr("data-type");
        if (res_type == "all") {
            $(".contribution").fadeIn();
        }
        else {
            $(".contribution").hide();
            $(".contribution[data-type='" + res_type + "']").fadeIn();
        }
    });

    // Initialize filters
    var collection = [];
    collection["total"] = 0;

    var rows = $(".contribution");
    for (var i = 0; i < rows.length; i++) {
        if (collection[$(rows[i]).attr("data-type")]) {
            collection[$(rows[i]).attr("data-type")]++;
        }
        else {
            collection[$(rows[i]).attr("data-type")] = 1;
        }
        collection["total"]++;
    }

    for (var item in collection) {
        $("tr[data-type='" + item + "']").find(".badge").text(collection[item]);
    }

    $("tr[data-type='all']").find(".badge").text(collection["total"]);


    // Unspecified goes away as soon as a user clicks.
    $("input[name='state']").click(function () {
            if ($(this).val() == "Unspecified") {
                $(this).val("");
            }
        }
    );

    $('.tagsinput').tagsInput({
      interactive: true,
      placeholder: "Organization(s)",
      autocomplete: {
        source: "/hsapi/dictionary/universities/",
        minLength: 3,
        delay: 500,
        classes: {
            "ui-autocomplete": "minHeight"
        }
      }
    });

    $('.ui-autocomplete-input').on('blur', function(e) {
      e.preventDefault();
      $('.ui-autocomplete-input').trigger(jQuery.Event('keypress', { which: 13 }));
    });

    $('.ui-autocomplete-input').on('keydown', function(e) {
      if(e.keyCode === 9 && $(this).val() !== '') {
        e.preventDefault();
        $(this).trigger(jQuery.Event('keypress', { which: 13 }));
      }
    });
});

