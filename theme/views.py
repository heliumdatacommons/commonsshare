from json import dumps, loads
import requests
import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib.messages import info
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.http import int_to_base36
from django.template.response import TemplateResponse
from rest_framework import status

from mezzanine.conf import settings
from mezzanine.generic.views import initial_validation
from mezzanine.utils.views import set_cookie, is_spam
from mezzanine.utils.cache import add_cache_bypass
from mezzanine.utils.email import send_verification_mail, send_approve_mail, subject_template, \
    default_token_generator, send_mail_template
from mezzanine.utils.urls import login_redirect, next_url
from mezzanine.accounts.forms import LoginForm
from django.shortcuts import render
from django.core.exceptions import PermissionDenied

from hs_core.hydroshare.utils import user_from_id
from hs_access_control.models import GroupMembershipRequest
from hs_dictionary.models import University, UncategorizedTerm
from theme.forms import ThreadedCommentForm
from theme.forms import RatingForm, UserProfileForm, UserForm
from theme.models import UserProfile
from theme.utils import get_quota_message

from .forms import SignupForm


logger = logging.getLogger(__name__)


def get_user_profile_context_data(pu, request=None):
    # get all resources the profile user owns
    resources = pu.uaccess.owned_resources
    # get a list of groupmembershiprequests
    group_membership_requests = GroupMembershipRequest.objects.filter(invitation_to=pu).all()

    # if requesting user is not the profile user, then show only resources that the requesting user has access
    if request and request.user != pu:
        if request.user.is_authenticated():
            if request.user.is_superuser:
                # admin can see all resources owned by profile user
                pass
            else:
                # filter out any resources the requesting user doesn't have access
                resources = resources.filter(Q(pk__in=request.user.uaccess.view_resources) |
                                             Q(raccess__public=True) | Q(raccess__discoverable=True))

        else:
            # for anonymous requesting user show only resources that are either public or discoverable
            resources = resources.filter(Q(raccess__public=True) | Q(raccess__discoverable=True))

    context_dict = {
        'profile_user': pu,
        'resources': resources,
        'quota_message': get_quota_message(pu),
        'group_membership_requests': group_membership_requests,
    }

    if request and 'subject_id' in request.session:
        context_dict['uid'] = request.session['subject_id']

    return context_dict


class UserProfileView(TemplateView):
    template_name='accounts/profile.html'

    def get_context_data(self, **kwargs):
        if 'user' in kwargs:
            try:
                u = User.objects.get(pk=int(kwargs['user']))
            except:
                u = User.objects.get(username=kwargs['user'])
        else:
            try:
                u = User.objects.get(pk=int(self.request.GET['user']))
            except:
                u = User.objects.get(username=self.request.GET['user'])

        return get_user_profile_context_data(u, self.request)


class UserPasswordResetView(TemplateView):
    template_name = 'accounts/reset_password.html'

    def get_context_data(self, **kwargs):
        token = kwargs.pop('token', None)
        if token is None:
            raise ValidationError('Unauthorised access to reset password')
        context = super(UserPasswordResetView, self).get_context_data(**kwargs)
        return context


# added by Hong Yi to address issue #186 to customize Mezzanine-based commenting form and view
def comment(request, template="generic/comments.html"):
    """
    Handle a ``ThreadedCommentForm`` submission and redirect back to its
    related object.
    """
    response = initial_validation(request, "comment")
    if isinstance(response, HttpResponse):
        return response
    obj, post_data = response
    resource_mode = post_data.get('resource-mode', 'view')
    request.session['resource-mode'] = resource_mode
    form = ThreadedCommentForm(request, obj, post_data)
    if form.is_valid():
        url = obj.get_absolute_url()
        if is_spam(request, form, url):
            return redirect(url)
        comment = form.save(request)
        response = redirect(add_cache_bypass(comment.get_absolute_url()))
        # Store commenter's details in a cookie for 90 days.
        # for field in ThreadedCommentForm.cookie_fields:
        #     cookie_name = ThreadedCommentForm.cookie_prefix + field
        #     cookie_value = post_data.get(field, "")
        #     set_cookie(response, cookie_name, cookie_value)
        return response
    elif request.is_ajax() and form.errors:
        return HttpResponse(dumps({"errors": form.errors}))
    # Show errors with stand-alone comment form.
    context = {"obj": obj, "posted_comment_form": form}
    response = render(request, template, context)
    return response


# added by Hong Yi to address issue #186 to customize Mezzanine-based rating form and view
def rating(request):
    """
    Handle a ``RatingForm`` submission and redirect back to its
    related object.
    """
    response = initial_validation(request, "rating")
    if isinstance(response, HttpResponse):
        return response
    obj, post_data = response
    url = add_cache_bypass(obj.get_absolute_url().split("#")[0])
    response = redirect(url + "#rating-%s" % obj.id)
    resource_mode = post_data.get('resource-mode', 'view')
    request.session['resource-mode'] = resource_mode
    rating_form = RatingForm(request, obj, post_data)
    if rating_form.is_valid():
        rating_form.save()
        if request.is_ajax():
            # Reload the object and return the rating fields as json.
            obj = obj.__class__.objects.get(id=obj.id)
            rating_name = obj.get_ratingfield_name()
            json = {}
            for f in ("average", "count", "sum"):
                json["rating_" + f] = getattr(obj, "%s_%s" % (rating_name, f))
            response = HttpResponse(dumps(json))
        ratings = ",".join(rating_form.previous + [rating_form.current])
        set_cookie(response, "mezzanine-rating", ratings)
    return response


def signup(request, template="accounts/account_signup.html", extra_context=None):
    """
    Signup form. Overriding mezzanine's view function for signup submit
    """
    form = SignupForm(request, request.POST, request.FILES)
    if request.method == "POST" and form.is_valid():
        try:
            new_user = form.save()
        except ValidationError as e:
            messages.error(request, e.message)
            return HttpResponseRedirect(request.META['HTTP_REFERER'])
        else:
            if not new_user.is_active:
                if settings.ACCOUNTS_APPROVAL_REQUIRED:
                    send_approve_mail(request, new_user)
                    info(request, _("Thanks for signing up! You'll receive "
                                    "an email when your account is activated."))
                else:
                    send_verification_mail(request, new_user, "signup_verify")
                    info(request, _("A verification email has been sent to " + new_user.email +
                                    " with a link that must be clicked prior to your account "
                                    "being activated. If you do not receive this email please "
                                    "check that you entered your address correctly, or your " 
                                    "spam folder as sometimes the email gets flagged as spam. "
                                    "If you entered an incorrect email address, please request "
                                    "an account again."))
                return redirect(next_url(request) or "/")
            else:
                info(request, _("Successfully signed up"))
                auth_login(request, new_user)
                return login_redirect(request)

    # remove the key 'response' from errors as the user would have no idea what it means
    form.errors.pop('response', None)
    messages.error(request, form.errors)

    # TODO: User entered data could be retained only if the following
    # render function would work without messing up the css

    # context = {
    #     "form": form,
    #     "title": _("Sign up"),
    # }
    # context.update(extra_context or {})
    # return render(request, template, context)

    # This one keeps the css but not able to retained user entered data.
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def update_user_profile(request):
    user = request.user
    old_email = user.email
    user_form = UserForm(request.POST, instance=user)
    user_profile = UserProfile.objects.filter(user=user).first()

    dict_items = request.POST['organization'].split(",")
    for dict_item in dict_items:
        # Update Dictionaries
        try:
            University.objects.get(name=dict_item)
        except ObjectDoesNotExist:
            new_term = UncategorizedTerm(name=dict_item)
            new_term.save()

    profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
    try:
        with transaction.atomic():
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile = profile_form.save(commit=False)
                profile.user = request.user
                profile.save()
                messages.success(request, "Your profile has been successfully updated.")
                # if email was updated, reset to old email and send confirmation
                # email to the user's new email - email will be updated upon confirmation
                if old_email != user.email:
                    new_email = user.email
                    user.email = old_email
                    user.save()
                    # send a confirmation email to the new email address
                    send_verification_mail_for_email_update(request, user, new_email, "email_verify")
                    info(request, _("A verification email has been sent to your new email with "
                                    "a link for updating your email. If you "
                                    "do not receive this email please check your "
                                    "spam folder as sometimes the confirmation email "
                                    "gets flagged as spam. If you entered an incorrect "
                                    "email address, please request email update again. "
                                    ))
                    # send an email to the old address notifying the email change
                    message = """Dear {}
                    <p>CommonsShare received a request to change the email address associated with
                    CommonsShare account {} from {} to {}. You are receiving this email to the old
                    email address as a precaution. If this is correct you may ignore this email
                    and click on the link in the email sent to the new address to confirm this change.</p>
                    <p>If you did not originate this request, there is a danger someone else has
                    accessed your account. You should log into CommonsShare, change your password,
                    and set the email address to the correct address. If you are unable to do this
                    contact help@cuahsi.org
                    <p>Thank you</p>
                    <p>The CommonsShare Team</p>
                    """.format(user.first_name, user.username, user.email, new_email)
                    send_mail(subject="Change of CommonsShare email address.",
                              message=message,
                              html_message=message,
                              from_email= settings.DEFAULT_FROM_EMAIL, recipient_list=[old_email],
                              fail_silently=True)
            else:
                errors = {}
                if not user_form.is_valid():
                    errors.update(user_form.errors)

                if not profile_form.is_valid():
                    errors.update(profile_form.errors)

                msg = ' '.join([err[0] for err in errors.values()])
                messages.error(request, msg)

    except Exception as ex:
        messages.error(request, ex.message)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def request_password_reset(request):
    username_or_email = request.POST['username']
    try:
        user = user_from_id(username_or_email)
    except Exception as ex:
        messages.error(request, "No user is found for the provided username or email")
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    messages.info(request,
                  _("A verification email has been sent to your email with "
                    "a link for resetting your password. If you "
                    "do not receive this email please check your "
                    "spam folder as sometimes the confirmation email "
                    "gets flagged as spam."
                    ))

    # send an email to the the user notifying the password reset request
    send_verification_mail_for_password_reset(request, user)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def update_user_password(request):
    user = request.user
    old_password = request.POST['password']
    password1 = request.POST['password1']
    password2 = request.POST['password2']
    password1 = password1.strip()
    password2 = password2.strip()
    if not user.check_password(old_password):
        messages.error(request, "Your current password does not match.")
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    if len(password1) < 6:
        messages.error(request, "Password must be at least 6 characters long.")
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    if password1 == password2:
        user.set_password(password1)
        user.save()
    else:
        messages.error(request, "Passwords do not match.")
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    messages.info(request, 'Password reset was successful')
    return HttpResponseRedirect('/user/{}/'.format(user.id))


@login_required
def reset_user_password(request):
    user = request.user
    password1 = request.POST['password1']
    password2 = request.POST['password2']
    password1 = password1.strip()
    password2 = password2.strip()

    if len(password1) < 6:
        messages.error(request, "Password must be at least 6 characters long.")
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    if password1 == password2:
        user.set_password(password1)
        user.save()
    else:
        messages.error(request, "Passwords do not match.")
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    messages.info(request, 'Password reset was successful')
    # redirect to home page
    return HttpResponseRedirect('/')


def send_verification_mail_for_email_update(request, user, new_email, verification_type):
    """
    Sends an email with a verification link to users when
    they update their email. The email is sent to the new email.
    The actual update of the email happens only after
    the verification link is clicked.
    The ``verification_type`` arg is both the name of the urlpattern for
    the verification link, as well as the names of the email templates
    to use.
    """
    verify_url = reverse(verification_type, kwargs={
        "uidb36": int_to_base36(user.id),
        "token": default_token_generator.make_token(user),
        "new_email": new_email
    }) + "?next=" + (next_url(request) or "/")
    context = {
        "request": request,
        "user": user,
        "new_email": new_email,
        "verify_url": verify_url,
    }
    subject_template_name = "email/%s_subject.txt" % verification_type
    subject = subject_template(subject_template_name, context)
    send_mail_template(subject, "email/%s" % verification_type,
                       settings.DEFAULT_FROM_EMAIL, new_email,
                       context=context)


def send_verification_mail_for_password_reset(request, user):
    """
    Sends an email with a verification link to users when
    they request to reset forgotten password to their email. The email is sent to the new email.
    The actual reset of of password will begin after the user clicks the link
    provided in the email.
    The ``verification_type`` arg is both the name of the urlpattern for
    the verification link, as well as the names of the email templates
    to use.
    """
    reset_url = reverse('email_verify_password_reset', kwargs={
        "uidb36": int_to_base36(user.id),
        "token": default_token_generator.make_token(user)
    }) + "?next=" + (next_url(request) or "/")
    context = {
        "request": request,
        "user": user,
        "reset_url": reset_url
    }
    subject_template_name = "email/reset_password_subject.txt"
    subject = subject_template(subject_template_name, context)
    send_mail_template(subject, "email/reset_password",
                       settings.DEFAULT_FROM_EMAIL, user.email,
                       context=context)


def oauth_request(request):
    # note that trailing slash should not be added to return_to url
    return_url = '&return_to={}://{}/oauth_return'.format(request.scheme, request.get_host())
    url = '{}authorize?provider=auth0&scope=openid%20email%20profile{}'.format(settings.OAUTH_SERVICE_SERVER_URL, return_url)
    auth_header_str = 'Basic {}'.format(settings.OAUTH_APP_KEY)
    response = requests.get(url,
                            headers={'Authorization': auth_header_str},
                            verify=False)
    if response.status_code != status.HTTP_200_OK:
        return HttpResponseBadRequest(content=response.text)
    return_data = loads(response.content)

    auth_url = return_data['authorization_url']

    return HttpResponseRedirect(auth_url)


def oauth_return(request):
    token = request.GET.get('access_token', None)
    uid = request.GET.get('uid', None)
    uname = request.GET.get('user_name', None)
    uemail = request.GET.get('email', '')
    if not token or not uid or not uname:
        return HttpResponseBadRequest('Bad request - no valid access_token or uid or user_name is provided')

    name = request.GET.get('name', '')
    if name:
        namestrs = name.split(' ')
        fname = namestrs[0]
        lname = namestrs[-1]
    else:
        fname = ''
        lname = ''

    kwargs = {}
    kwargs['request'] = request
    kwargs['username'] = uname
    kwargs['access_token'] = token
    kwargs['first_name'] = fname
    kwargs['last_name'] = lname
    kwargs['email'] = uemail
    kwargs['uid'] = uid

    # authenticate against oauth with username and access_token and create linked user in CommonsShare
    try:
        tgt_user = authenticate(**kwargs)
    except PermissionDenied as ex:
        info(request, _(ex.message))
        return login_redirect(request)

    if tgt_user:
        login_msg = "Successfully logged in"
        auth_login(request, tgt_user)
        info(request, _(login_msg))
        request.session['subject_id'] = uid
        request.session['access_token'] = token
        return login_redirect(request)
    else:
        # info(request, _('You are not authorized to log in CommonsShare'))
        info(request, _('Dear user, you are trying to login but have yet to be added to the Data '
                        'Use Agreement whitelist. If you are an authorized user, you will receive '
                        'an email with a link inviting you to be added to the whitelist indicating '
                        'your acceptance of the Data Use Agreement.'))
        # send notification email to the list for user login monitoring
        if settings.WHITE_LIST_LOGIN and settings.WHITE_LIST_EMAIL:
            message = """Dear Administrator, 
                                <p>CommonsShare received a login attempt from a non-whitelisted 
                                user {} {} with username {} and email address {} </p>
                                <p>Please determine whether this user can be authorized to access 
                                CommonsShare and follow the onboarding process to invite the user 
                                to join a proper whitelist group in CommonsShare if needed. 
                                <p>Thank you</p>
                                <p>The CommonsShare Team</p>
                                """.format(fname, lname, uname, uemail)
            send_mail(subject="Notification of non-whitelisted user login attempt",
                      message=message,
                      html_message=message,
                      from_email=settings.DEFAULT_FROM_EMAIL,
                      recipient_list=[settings.WHITE_LIST_EMAIL],
                      fail_silently=True)

        return login_redirect(request)


@login_required
def generate_token(request, uid):
    lbl = request.POST.get('label', '')
    url = '{}apikey/{}/new'.format(settings.OAUTH_SERVICE_SERVER_URL, uid)
    auth_header_str = 'Basic {}'.format(settings.OAUTH_APP_KEY)
    response = requests.get(url, params={'label': lbl}, headers={'Authorization': auth_header_str})
    if response.status_code != status.HTTP_200_OK:
        return JsonResponse({'message': response.text}, status=response.status_code)
    return_data = loads(response.content)

    response_data = {}
    response_data['result'] = return_data['key']
    response_data['label'] =  lbl

    return JsonResponse(response_data, status=status.HTTP_200_OK)


@login_required
def get_all_tokens(request, uid):
    url = '{}apikey/{}'.format(settings.OAUTH_SERVICE_SERVER_URL, uid)
    auth_header_str = 'Basic {}'.format(settings.OAUTH_APP_KEY)
    response = requests.get(url, headers={'Authorization': auth_header_str})
    if response.status_code != status.HTTP_200_OK:
        return JsonResponse({'message': response.text}, status=response.status_code)

    return_data = loads(response.content)
    response_data = {}
    response_data["results"] = []
    if 'keys' in return_data:
        for key in return_data['keys']:
            response_data['results'].append({
                "id": key['id'],
                "hash": key['hash'],
                "label": key['label'],
                "creation_time": key['creation_time']
            })

    return JsonResponse(response_data, status=status.HTTP_200_OK)


@login_required
def delete_all_tokens(request, uid):
    url = '{}apikey/{}'.format(settings.OAUTH_SERVICE_SERVER_URL, uid)
    auth_header_str = 'Basic {}'.format(settings.OAUTH_APP_KEY)
    tokens_list_str = request.POST.get('tokens', '')

    if not tokens_list_str:
        return JsonResponse({'message': 'Please select tokens to revoke'},
                            status=status.HTTP_200_OK)

    deleted_token_list = []
    tokens_list = loads(tokens_list_str)
    for token_dict in tokens_list:
        key = token_dict.get('key', '')
        value = token_dict.get('value', '')
        if key and value:
            response = requests.delete(url + '/' + key, headers={'Authorization': auth_header_str})
            if response.status_code != status.HTTP_200_OK:
                logger.debug("Failed to delete selected token " + key + ": " + response.text)
                continue
            else:
                deleted_token_list.append(value)

    if not deleted_token_list:
        ret_msg = 'Server error: selected tokens cannot be deleted successfully. ' \
                  'Check server log for details'
    elif len(deleted_token_list) == len(tokens_list):
        if len(deleted_token_list) == 1:
            ret_msg = "The selected token has been deleted successfully."
        else:
            ret_msg = "All selected tokens have been deleted successfully."
    else:
        ret_msg = "Only the following subset of selected tokens are deleted successfully: "
        ret_msg += ','.join(deleted_token_list)

    return JsonResponse({'message': ret_msg}, status=status.HTTP_200_OK)


@login_required
def retrieve_globus_buckets(request):
    # note that trailing slash should not be added to return_to url
    return_url = '&return_to={}://{}/gdo_return'.format(request.scheme, request.get_host())
    uid = request.session.get('subject_id', '')
    if not uid:
        return HttpResponseBadRequest(content='user subject id is empty')

    url = 'token?uid={}&provider=globus&scope=urn:globus:auth:scope:transfer.api.globus.org:all'.format(uid)
    req_url = '{}{}{}'.format(settings.OAUTH_SERVICE_SERVER_URL, url, return_url)

    auth_header_str = 'Basic {}'.format(settings.OAUTH_APP_KEY)
    response = requests.get(req_url,
                            headers={'Authorization': auth_header_str},
                            verify=False)
    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        # the user is not authorized - need to authorize the user
        return_data = loads(response.text)
        auth_url = return_data['authorization_url']
        return HttpResponseRedirect(auth_url)
    elif response.status_code == status.HTTP_200_OK:
        # the user is already authorized, directly use the returned token
        return_data = loads(response.content)
        if 'access_token' in return_data:
            atoken = return_data['access_token']
            full_ret_url = '{}?access_token={}'.format('/gdo_return', atoken)
            return HttpResponseRedirect(full_ret_url)
        else:
            return HttpResponseBadRequest('no access_token is returned from token request:' + response.content)
    else:
        return HttpResponseBadRequest(content=response.text)


@login_required
def globus_data_auth_return(request):
    token = request.GET.get('access_token', None)
    if not token:
        return HttpResponseBadRequest('Bad request - no valid access_token is provided')

    # get avaiable endpoints for a given globus user
    url = '{}registration/get_buckets?provider=globus&token={}'.format(settings.DATA_REG_SERVICE_SERVER_URL, token)
    auth_header_str = 'Basic {}'.format(settings.DATA_REG_API_KEY)
    response = requests.get(url,
                            headers={'Authorization': auth_header_str},
                            verify=False)
    if response.status_code != status.HTTP_200_OK:
        # request fails
        return HttpResponseBadRequest('Bad request - the data registration service cannot list avaiable endpoints: ' +
                                      response.content)
    return_data = loads(response.content)
    bucket_list = return_data['buckets']
    ep_list = []
    for bucket in bucket_list:
        ep_list.append({'name': bucket['name'], 'id': bucket['id']})

    # /return to user profile page
    template_name = 'accounts/profile.html'
    context = get_user_profile_context_data(request.user, request)
    context['endpoints'] = ep_list
    context['globus_token'] = token
    return TemplateResponse(request, template_name, context)


def login(request, template="accounts/account_login.html",
          form_class=LoginForm, extra_context=None):
    """
    Login form - customized from Mezzanine login form so that quota warning message can be
    displayed when the user is logged in.
    """
    form = form_class(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login_msg = "Successfully logged in"
        authenticated_user = form.save()
        add_msg = get_quota_message(authenticated_user)
        if add_msg:
            login_msg += ' - ' + add_msg
        info(request, _(login_msg))
        auth_login(request, authenticated_user)
        return login_redirect(request)
    context = {"form": form, "title": _("Log in")}
    context.update(extra_context or {})
    return TemplateResponse(request, template, context)


def email_verify(request, new_email, uidb36=None, token=None):
    """
    View for the link in the verification email sent to a user
    when they update their email as part of profile update.
    User email is set to new_email and logs them in,
    redirecting to the URL they tried to access profile.
    """

    user = authenticate(uidb36=uidb36, token=token, is_active=True)
    if user is not None:
        user.email = new_email
        user.save()
        auth_login(request, user)
        messages.info(request, _("Successfully updated email"))
        # redirect to user profile page
        return HttpResponseRedirect('/user/{}/'.format(user.id))
    else:
        messages.error(request, _("The link you clicked is no longer valid."))
        return redirect("/")


def email_verify_password_reset(request, uidb36=None, token=None):
    """
    View for the link in the reset password email sent to a user
    when they clicked the forgot password link.
    User is redirected to password reset page where the user can enter new password.
    """

    user = authenticate(uidb36=uidb36, token=token, is_active=True)
    if user is not None:
        auth_login(request, user)
        # redirect to user to password reset page
        return HttpResponseRedirect(reverse('new_password_for_reset', kwargs={'token': token}))
    else:
        messages.error(request, _("The link you clicked is no longer valid."))
        return redirect("/")
