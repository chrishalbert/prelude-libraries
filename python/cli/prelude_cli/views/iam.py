import click

from rich import print_json
from datetime import datetime, timedelta

from prelude_sdk.models.codes import AuditEvent, Mode, Permission
from prelude_cli.views.shared import handle_api_error, Spinner
from prelude_sdk.controllers.iam_controller import IAMController


@click.group()
@click.pass_context
def iam(ctx):
    """ Prelude account management """
    ctx.obj = IAMController(account=ctx.obj)


@iam.command('create-account')
@click.pass_obj
@handle_api_error
@click.confirmation_option(prompt='Overwrite local account credentials for selected profile?')
def register_account(controller):
    """ Register a new account """
    email = click.prompt('Enter your email')
    name = click.prompt('(Optional) Enter your name', default='', show_default=False)
    company = click.prompt('(Optional) Enter your associated company', default='', show_default=False)
    with Spinner(description='Creating new account'):
        data = controller.new_account(user_email=email, user_name=name, company=company)
    print_json(data=data)
    print("\nCheck your email to verify your account.\n")


@iam.command('update-account')
@click.option('-m', '--mode',
              help='provide a mode',
              default=None, show_default=False,
              type=click.Choice([m.name for m in Mode], case_sensitive=False))
@click.option('-c', '--company', help='provide your associated company', default=None, show_default=False, type=str)
@click.pass_obj
@handle_api_error
def update_account(controller, mode, company):
    """ Update an account """
    with Spinner(description='Updating account information'):
        data = controller.update_account(
            mode=Mode[mode] if mode else None,
            company=company
        )
    print_json(data=data)


@iam.command('attach-oidc')
@click.argument('issuer',
                type=click.Choice(['google', 'azure', 'okta'], case_sensitive=False))
@click.option('--client_id', required=True, help='Client ID')
@click.option('--client_secret', required=True, help='Client secret')
@click.option('--oidc_config_url', required=True, help='Configuration endpoint')
@click.pass_obj
@handle_api_error
def attach_oidc(controller, issuer, client_id, client_secret, oidc_config_url):
    """ Attach OIDC to an account """
    with Spinner(description='Attaching OIDC'):
        data = controller.attach_oidc(
            issuer=issuer,
            client_id=client_id,
            client_secret=client_secret,
            oidc_config_url=oidc_config_url
        )
    print_json(data=data)


@iam.command('detach-oidc')
@click.pass_obj
@handle_api_error
def detach_oidc(controller):
    """ Detach OIDC to an account """
    with Spinner(description='Detaching OIDC'):
        data = controller.detach_oidc()
    print_json(data=data)


@iam.command('account')
@click.pass_obj
@handle_api_error
def describe_account(controller):
    """ Get account details """
    with Spinner(description='Fetching account details'):
        data = controller.get_account()
    print_json(data=data)


@iam.command('create-user')
@click.option('-d', '--days', help='days this user will remain active', default=365, type=int)
@click.option('-p', '--permission', help='user permission level', default=Permission.SERVICE.name,
              type=click.Choice([p.name for p in Permission if p != Permission.INVALID], case_sensitive=False), show_default=True)
@click.option('-n', '--name', help='name of user', default=None, show_default=False, type=str)
@click.option('-o', '--oidc', help='whether user must login via SSO', is_flag=True)
@click.argument('email')
@click.pass_obj
@handle_api_error
def create_user(controller, days, permission, name, oidc, email):
    """ Create a new user in your account """
    expires = datetime.utcnow() + timedelta(days=days)
    with Spinner(description='Creating new user'):
        data = controller.create_user(
            email=email,
            permission=Permission[permission],
            name=name,
            expires=expires,
            oidc=oidc
        )
    print_json(data=data)
    if permission != Permission.SERVICE.name:
        print("\nNew user must check their email to verify their account.\n")


@iam.command('reset-password')
@click.argument('email')
@click.option('-a', '--account', help='override the profile account id', default=None, show_default=False, type=str)
@click.pass_obj
def reset_password(controller, email, account):
    """ Reset a user's password """
    with Spinner(description='Resetting password'):
        controller.reset_password(email=email, account_id=account)
    print("\nCheck your email to for the reset token.\n")
    
    token = click.prompt('Enter your reset token', type=str)
    with Spinner(description='Retrieving new password'):
        data = controller.verify_user(token=token)
    print_json(data=data)



@iam.command('delete-user')
@click.confirmation_option(prompt='Are you sure?')
@click.argument('handle')
@click.pass_obj
@handle_api_error
def delete_user(controller, handle):
    """ Remove a user from your account """
    with Spinner(description='Deleting user'):
        data = controller.delete_user(handle=handle)
    print_json(data=data)


@iam.command('logs')
@click.option('-d', '--days', help='days back to search from today', default=7, type=int)
@click.option('-l', '--limit', help='limit the number of results', default=1000, type=int)
@click.pass_obj
@handle_api_error
def logs(controller, days, limit):
    """ Get audit logs """
    with Spinner(description='Fetching logs'):
        data = controller.audit_logs(days=days, limit=limit)
    print_json(data=data)


@iam.command('subscribe')
@click.argument('event',
                type=click.Choice([e.name for e in AuditEvent if e != AuditEvent.INVALID], case_sensitive=False))
@click.pass_obj
@handle_api_error
def subscribe(controller, event):
    """ Subscribe to email notifications for an event """
    with Spinner(description='Subscribing'):
        data = controller.subscribe(event=AuditEvent[event])
    print_json(data=data)


@iam.command('unsubscribe')
@click.argument('event',
                type=click.Choice([e.name for e in AuditEvent if e != AuditEvent.INVALID], case_sensitive=False))
@click.pass_obj
@handle_api_error
def unsubscribe(controller, event):
    """ Unsubscribe to email notifications for an event """
    with Spinner(description='Unsubscribing'):
        data = controller.unsubscribe(event=AuditEvent[event])
    print_json(data=data)


@iam.command('purge')
@click.confirmation_option(prompt='Are you sure?')
@click.pass_obj
@handle_api_error
def purge(controller):
    """ Delete your account """
    with Spinner(description='Purging account from existence'):
        data = controller.purge_account()
    print_json(data=data)
