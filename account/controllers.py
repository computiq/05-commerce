from django.contrib.auth import get_user_model, authenticate
from django.shortcuts import get_object_or_404
from ninja import Router


from account.authorization import GlobalAuth, get_tokens_for_user
from account.schemas import AccountCreate, AuthOut, SigninSchema, AccountOut, AccountUpdate, ChangePasswordSchema
from config.utils.schemas import MessageOut

from config.utils.decorators import check_pk

User = get_user_model()


account_controller = Router(tags=['auth'])

@account_controller.post('signup', response={
    400: MessageOut,
    201: AuthOut,
})
def signup(request, account_in: AccountCreate):
    if account_in.password1 != account_in.password2:
        return 400, {'detail': 'Passwords do not match!'}

    try:
        User.objects.get(email=account_in.email)
    except User.DoesNotExist:
        new_user = User.objects.create_user(
            first_name=account_in.first_name,
            last_name=account_in.last_name,
            email=account_in.email,
            password=account_in.password1
        )

        token = get_tokens_for_user(new_user)

        return 201, {
            'token': token,
            'account': new_user,
        }

    return 400, {'detail': 'User already registered!'}


@account_controller.post('signin', response={
    200: AuthOut,
    404: MessageOut,
})
def signin(request, signin_in: SigninSchema):
    user = authenticate(email=signin_in.email, password=signin_in.password)

    if not user:
        return 404, {'detail': 'User does not exist'}

    token = get_tokens_for_user(user)

    return {
        'token': token,
        'account': user
    }


@account_controller.get('', auth=GlobalAuth(), response={200: AccountOut, 401: MessageOut})
@check_pk
def me(request):
    return User.objects.get(id=request.auth['pk'])


@account_controller.put('', auth=GlobalAuth(), response={
    200: AccountOut,
    401: MessageOut
})
@check_pk
def update_account(request, update_in: AccountUpdate):
    User.objects.filter(id=request.auth['pk']).update(**update_in.dict())
    return User.objects.get(id=request.auth['pk'])


@account_controller.post('change-password', auth=GlobalAuth(), response={
    200: MessageOut,
    400: MessageOut,
    401: MessageOut
})
@check_pk
def change_password(request, password_update_in: ChangePasswordSchema):

    if password_update_in.new_password1 != password_update_in.new_password2:
        return 400, {'detail': 'passwords do not match'}
    user = User.objects.get(id=request.auth['pk'])
    is_it_him = user.check_password(password_update_in.old_password)

    if not is_it_him:
        return 400, {'detail': 'Dude, make sure you are him!'}

    user.set_password(password_update_in.new_password1)
    user.save()
    return {'detail': 'password updated successfully'}