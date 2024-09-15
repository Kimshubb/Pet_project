#this function creates the root user for a specific school 
# using flask create-admin
# or flask create-admin --username admin --email admin@example.com --school-name "Example School" --school-contacts "123-456-7890" 
import click
from flask.cli import with_appcontext
from jps_erp import db
from jps_erp.models import User, School  # Adjust this import based on where your models are defined
from sqlalchemy.exc import IntegrityError

@click.command('create-admin')
@click.option('--username', prompt=True, help="Admin username")
@click.option('--email', prompt=True, help="Admin email")
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help="Admin password")
@click.option('--school-name', prompt=True, help="School name")
@click.option('--school-contacts', prompt=True, help="School contacts")
@with_appcontext
def create_admin(username, email, password, school_name, school_contacts):
    """Create a new admin user."""
    try:
        # Check if user already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            if existing_user.username == username:
                click.echo('Error: Username already exists.')
            else:
                click.echo('Error: Email already exists.')
            return

        # Create or get school
        school = School.query.filter_by(name=school_name).first()
        if not school:
            school = School(name=school_name, contacts=school_contacts)
            db.session.add(school)
            db.session.flush()

        # Create new admin user
        new_admin = User(
            username=username,
            email=email,
            role='admin',
            school_id=school.school_id
        )
        new_admin.set_password(password)

        db.session.add(new_admin)
        db.session.commit()

        click.echo(f'Admin user {username} created successfully.')

    except IntegrityError:
        db.session.rollback()
        click.echo('Error: Database integrity error. The user or school may already exist.')
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error: An unexpected error occurred: {str(e)}')

def register_commands(app):
    app.cli.add_command(create_admin)