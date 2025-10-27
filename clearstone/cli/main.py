"""
Command-line interface for Clearstone SDK.
"""

import click
from pathlib import Path


POLICY_TEMPLATE = """\
# {filepath}
from clearstone import Policy, ALLOW, BLOCK, Decision
from clearstone.core.context import PolicyContext

@Policy(name="{policy_name}", priority={priority})
def {function_name}(context: PolicyContext) -> Decision:
    \"\"\"
    [TODO: Describe what this policy does.]
    
    Required Metadata:
        - [TODO: List the context.metadata keys this policy needs.]
    \"\"\"
    
    # [TODO: Implement your policy logic here.]
    # Example:
    # role = context.metadata.get("role")
    # if role == "guest":
    #     return BLOCK("Guests are not allowed.")

    return ALLOW
"""


@click.group()
def cli():
    """Clearstone SDK Command-Line Interface."""
    pass


@cli.command("new-policy")
@click.argument("name", type=str)
@click.option(
    "--priority", type=int, default=0, help="Execution priority (higher runs first)."
)
@click.option("--dir", default="policies", help="Directory to save the policy file in.")
@click.option("--force", is_flag=True, help="Overwrite the file if it already exists.")
def new_policy(name: str, priority: int, dir: str, force: bool):
    """
    Creates a new policy boilerplate file.

    NAME: The unique name for the policy (e.g., 'enforce_spending_limit').

    Example:
        clearstone new-policy my-first-policy --priority=100
    """
    click.echo(f"Scaffolding new policy '{name}'...")

    function_name = name.lower().replace("-", "_") + "_policy"
    file_name = function_name + ".py"

    target_dir = Path(dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    filepath = target_dir / file_name

    if filepath.exists() and not force:
        click.secho(
            f"Error: File '{filepath}' already exists. Use --force to overwrite.",
            fg="red",
        )
        return

    content = POLICY_TEMPLATE.format(
        filepath=filepath,
        policy_name=name,
        priority=priority,
        function_name=function_name,
    )

    try:
        with open(filepath, "w") as f:
            f.write(content)
        click.secho(f"✓ Successfully created policy file at '{filepath}'", fg="green")
    except IOError as e:
        click.secho(
            f"Error: Could not write to file '{filepath}'. Reason: {e}", fg="red"
        )


if __name__ == "__main__":
    cli()
