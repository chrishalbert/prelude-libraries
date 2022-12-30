import importlib.resources as pkg_resources
import uuid
from pathlib import Path

import click
import prelude_cli.templates as templates
from prelude_cli.views.shared import handle_api_error
from prelude_sdk.models.codes import Colors
from rich import print_json

from prelude_sdk.controllers.build_controller import BuildController


@click.group()
@click.pass_context
def build(ctx):
    """ Terminal-based security test environment """
    ctx.obj = BuildController(account=ctx.obj)


@build.command('clone')
@click.pass_obj
@handle_api_error
def clone(controller):
    """ Download all tests to your local environment """
    Path('prelude').mkdir(exist_ok=True)
    for test in controller.list_tests():
        code = controller.download_test(name=test['name'])
        with open(f'prelude/{test["name"]}', 'wb') as test_code:
            test_code.write(code)
        click.secho(f'Cloned {test["id"]}')
    click.secho('Project cloned successfully', fg=Colors.GREEN.value)

@build.command('list-tests')
@click.pass_obj
@handle_api_error
def list_tests(controller):
    """ List all security tests """
    print_json(data=controller.list_tests())


@build.command('create-test')
@click.argument('question')
@click.pass_obj
@handle_api_error
def create_test(controller, question):
    """ Create a new security test """
    test_id = str(uuid.uuid4())
    basename = f'{test_id}.go'

    controller.create_test(test_id=test_id, question=question)
    template = pkg_resources.read_text(templates, 'template.go')
    controller.upload_test(name=basename, code=template)

    with open(basename, 'w') as test_code:
        test_code.write(template)
        click.secho(f'Created {basename}', fg=Colors.GREEN.value)


@build.command('delete-test')
@click.argument('test_id')
@click.confirmation_option(prompt='Are you sure?')
@click.pass_obj
@handle_api_error
def delete_test(controller, test_id):
    """ Delete TEST """
    controller.delete_test(test_id=test_id)
    click.secho(f'Deleted {test_id}', fg=Colors.GREEN.value)


@build.command('upload')
@click.argument('path', type=click.Path(exists=True))
@click.pass_obj
@handle_api_error
def save_test(controller, path):
    """ Upload a security test on disk """
    with open(path, 'r') as source_code:
        controller.upload_test(name=Path(path).name, code=source_code.read())
        click.secho(f'Uploaded {path}', fg=Colors.GREEN.value)


@build.command('url')
@click.argument('name')
@click.pass_obj
@handle_api_error
def create_url(controller, vst):
    """ Generate a download URL from a VST name """
    print_json(data=controller.create_url(vst=vst))


@build.command('compute')
@click.argument('name')
@click.pass_obj
@handle_api_error
def compute(controller, name):
    """ Create a VST from a test name """
    print_json(data=controller.compute(name=name))
