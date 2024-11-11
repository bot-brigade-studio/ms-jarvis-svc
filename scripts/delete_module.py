import os
import click
from typing import List
import re

class ModuleDeleter:
    def __init__(self, name: str):
        self.name = name
        self.snake_name = self.to_snake_case(name)
        self.files_to_delete = []
        self.init_files_to_update = []
        self.router_file = 'app/api/v1/router.py'

    @staticmethod
    def to_snake_case(name: str) -> str:
        """Convert CamelCase to snake_case"""
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

    def collect_files(self):
        """Collect all files related to the module"""
        self.files_to_delete = [
            f'app/models/{self.snake_name}.py',
            f'app/schemas/{self.snake_name}.py',
            f'app/repositories/{self.snake_name}.py',
            f'app/services/{self.snake_name}.py',
            f'app/api/v1/endpoints/{self.snake_name}.py',
        ]

        self.init_files_to_update = [
            'app/models/__init__.py',
            'app/schemas/__init__.py',
            'app/repositories/__init__.py',
            'app/services/__init__.py',
        ]

    def delete_files(self) -> List[str]:
        """Delete all module files"""
        deleted_files = []
        for file_path in self.files_to_delete:
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_files.append(file_path)
                click.echo(f"Deleted: {file_path}")
            else:
                click.echo(f"File not found: {file_path}")
        return deleted_files

    def update_init_files(self):
        """Remove imports from __init__.py files"""
        for init_file in self.init_files_to_update:
            if os.path.exists(init_file):
                with open(init_file, 'r') as f:
                    lines = f.readlines()
                
                # Remove the import line for this module
                new_lines = [
                    line for line in lines 
                    if not line.strip() == f"from .{self.snake_name} import *"
                ]
                
                with open(init_file, 'w') as f:
                    f.writelines(new_lines)
                
                click.echo(f"Updated: {init_file}")

    def update_router(self):
        """Remove router registration from main router"""
        if os.path.exists(self.router_file):
            with open(self.router_file, 'r') as f:
                lines = f.readlines()
            
            # Remove the import and router registration lines
            new_lines = []
            skip_next = False
            for line in lines:
                if skip_next:
                    skip_next = False
                    continue
                
                if f"from app.api.v1.endpoints import {self.snake_name}" in line:
                    continue
                if f"api_router.include_router({self.snake_name}.router" in line:
                    continue
                
                new_lines.append(line)
            
            with open(self.router_file, 'w') as f:
                f.writelines(new_lines)
            
            click.echo(f"Updated: {self.router_file}")

    def check_migrations(self) -> List[str]:
        """Check for related migration files"""
        migration_files = []
        migrations_dir = "alembic/versions"
        
        if os.path.exists(migrations_dir):
            for filename in os.listdir(migrations_dir):
                if filename.endswith('.py'):
                    file_path = os.path.join(migrations_dir, filename)
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if self.snake_name in content.lower():
                            migration_files.append(file_path)
        
        return migration_files

def confirm_deletion(ctx, param, value):
    if not value:
        ctx.abort()

@click.command()
@click.argument('name')
@click.option(
    '--force', '-f', 
    is_flag=True, 
    help='Force deletion without confirmation'
)
@click.option(
    '--check-only', 
    is_flag=True, 
    help='Only check what would be deleted without actually deleting'
)
@click.confirmation_option(
    prompt='Are you sure you want to delete this module?',
    help='Confirm deletion',
    callback=confirm_deletion
)
def delete_module(name: str, force: bool, check_only: bool):
    """Delete a module and all its related files"""
    deleter = ModuleDeleter(name)
    deleter.collect_files()

    # Check for existing files
    existing_files = [f for f in deleter.files_to_delete if os.path.exists(f)]
    if not existing_files:
        click.echo(f"No files found for module '{name}'")
        return

    # Check for migration files
    migration_files = deleter.check_migrations()

    if check_only:
        click.echo("\nFiles that would be deleted:")
        for file in existing_files:
            click.echo(f"  - {file}")
        
        if migration_files:
            click.echo("\nRelated migration files found:")
            for file in migration_files:
                click.echo(f"  - {file}")
        
        click.echo("\nInit files that would be updated:")
        for file in deleter.init_files_to_update:
            if os.path.exists(file):
                click.echo(f"  - {file}")
        
        if os.path.exists(deleter.router_file):
            click.echo(f"\nRouter file that would be updated:")
            click.echo(f"  - {deleter.router_file}")
        return

    # Perform deletion
    click.echo("\nDeleting module files...")
    deleter.delete_files()
    
    click.echo("\nUpdating __init__.py files...")
    deleter.update_init_files()
    
    click.echo("\nUpdating router...")
    deleter.update_router()

    if migration_files:
        click.echo("\nWarning: Related migration files found:")
        for file in migration_files:
            click.echo(f"  - {file}")
        click.echo("Please review and handle these migration files manually.")

    click.echo(f"\nSuccessfully deleted module '{name}'!")
    click.echo("\nNext steps:")
    click.echo("1. Review any remaining migration files")
    click.echo("2. Consider creating a new migration to remove the table:")
    # click.echo(f"   alembic revision -m \"remove_{deleter.snake_name}_table\"")
    # click.echo("3. Update your database schema accordingly")

if __name__ == '__main__':
    delete_module()