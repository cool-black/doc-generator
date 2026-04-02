"""DocGen interactive workflow runner.

Usage: python run.py
"""

from __future__ import annotations

import asyncio
import sys
import traceback
from pathlib import Path

# Fix Windows asyncio ProactorEventLoop issue with httpx
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Ensure project src is importable
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging
from doc_gen.utils.logger import setup_logging
setup_logging("INFO")

# Persistent event loop to avoid "Event loop is closed" errors
_loop = asyncio.new_event_loop()


def run_async(coro):  # type: ignore
    """Run an async coroutine on the persistent event loop."""
    return _loop.run_until_complete(coro)


def print_header() -> None:
    print("=" * 50)
    print("  DocGen - Document Generator")
    print("=" * 50)
    print()


def print_step(step: int, total: int, msg: str) -> None:
    print(f"\n[Step {step}/{total}] {msg}")
    print("-" * 40)


def print_error(msg: str) -> None:
    print(f"\n[ERROR] {msg}")


def print_success(msg: str) -> None:
    print(f"\n[OK] {msg}")


def input_choice(prompt: str, options: list[str], default: int = 1) -> int:
    """Show numbered options and return 1-based index."""
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        raw = input(f"{prompt} [{default}]: ").strip()
        if not raw:
            return default
        try:
            val = int(raw)
            if 1 <= val <= len(options):
                return val
        except ValueError:
            pass
        print(f"  Please enter 1-{len(options)}")


def check_env_file() -> bool:
    """Check .env file exists and has a real API key."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print_error(f".env file not found at: {env_path}")
        print("  Create it from the template and set your API key.")
        return False

    content = env_path.read_text(encoding="utf-8")
    if "sk-your-api-key-here" in content:
        print_error("API key not configured!")
        print(f"  Edit: {env_path}")
        print("  Set LLM_API_KEY to your actual API key.")
        return False

    return True


def prompt_output_dir(default_dir: Path) -> Path:
    """Prompt user for custom output directory, validate and create if needed."""
    print(f"\n  Default output directory: {default_dir}")
    print("  Press Enter to use default, or enter a custom path:")

    while True:
        user_input = input("  Output directory: ").strip()

        # Use default
        if not user_input:
            return default_dir

        try:
            path = Path(user_input).expanduser().resolve()

            # Check if parent directory exists
            parent = path.parent
            if not parent.exists():
                print_error(f"Parent directory does not exist: {parent}")
                print("  Please create the parent directory first, or use a different path.")
                continue

            # Check if parent is writable (try to create a test file)
            try:
                test_file = parent / ".write_test"
                test_file.touch()
                test_file.unlink()
            except (OSError, PermissionError):
                print_error(f"Cannot write to parent directory: {parent}")
                print("  Please check permissions or use a different path.")
                continue

            # Create the directory if it doesn't exist
            if not path.exists():
                try:
                    path.mkdir(parents=False, exist_ok=False)
                    print_success(f"Created directory: {path}")
                except (OSError, PermissionError) as e:
                    print_error(f"Failed to create directory: {e}")
                    continue

            return path

        except Exception as e:
            print_error(f"Invalid path: {e}")
            continue


def check_api_connection() -> bool:
    """Test LLM API connectivity."""
    print("  Testing API connection...")

    from doc_gen.config.loader import load_config
    from doc_gen.llm.client import LLMClient

    config = load_config()

    if not config.llm.api_key:
        print_error("No API key found. Check your .env file.")
        return False

    print(f"  Provider: {config.llm.provider.value}")
    print(f"  Model:    {config.llm.get_model()}")
    print(f"  Base URL: {config.llm.get_base_url()}")

    client = LLMClient(config.llm)

    async def _test():
        try:
            return await client.check_connection()
        finally:
            await client.close()

    success, message = run_async(_test())

    if success:
        print_success(message)
        return True
    else:
        print_error(message)
        return False


def step_create_project(project_name: str) -> bool:
    """Create project interactively. Returns True on success."""
    from doc_gen.cli.prompts import (
        prompt_doc_type,
        prompt_domain,
        prompt_files,
        prompt_granularity,
        prompt_audience,
        prompt_language,
    )
    from doc_gen.config.loader import ensure_data_dir, load_config
    from doc_gen.models.project import ProjectConfig
    from doc_gen.storage.database import Database
    from doc_gen.storage.project import ProjectStorage
    from doc_gen.storage.repository import ProjectRepository

    config = load_config()
    data_dir = ensure_data_dir(config)
    db = Database(data_dir / "db.sqlite")
    repo = ProjectRepository(db)
    storage = ProjectStorage(data_dir)

    # Check if already exists
    existing = repo.get_by_name(project_name)
    if existing:
        print(f"  Project '{project_name}' already exists (status: {existing.status.value})")
        choice = input_choice("Action?", [
            "Continue with existing project",
            "Delete and recreate",
        ])
        if choice == 1:
            return True
        else:
            storage.delete_project(existing.id)
            repo.delete(existing.id)
            print(f"  Deleted '{project_name}'.")

    try:
        domain = prompt_domain()
        doc_type = prompt_doc_type()
        audience = prompt_audience()
        granularity = prompt_granularity()
        language = prompt_language()

        # Ask for custom output directory
        default_output = data_dir / "output"
        output_dir = prompt_output_dir(default_output)

        project = ProjectConfig(
            name=project_name,
            domain=domain,
            doc_type=doc_type,
            audience=audience,
            granularity=granularity,
            language=language,
            output_dir=str(output_dir) if output_dir != default_output else None,
        )

        project_path = storage.create_project_dirs(project.id)
        upload_dir = project_path / "sources" / "uploaded"
        user_files = prompt_files(upload_dir)
        project.user_files = user_files

        repo.create(project)
        storage.save_meta(project)

        print_success(f"Project '{project_name}' created (ID: {project.id})")
        return True

    except (KeyboardInterrupt, EOFError):
        print("\n  Project creation cancelled.")
        return False
    except Exception as e:
        print_error(f"Failed to create project: {e}")
        return False


def step_generate_outline(project_name: str) -> bool:
    """Generate outline with user confirmation loop."""
    from doc_gen.cli.commands import _ensure_design_brief
    from doc_gen.cli.prompts import prompt_outline_action
    from doc_gen.config.loader import ensure_data_dir, load_config
    from doc_gen.core.generator import DocumentGenerator
    from doc_gen.models.project import ProjectStatus
    from doc_gen.storage.database import Database
    from doc_gen.storage.project import ProjectStorage
    from doc_gen.storage.repository import ProjectRepository

    config = load_config()
    data_dir = ensure_data_dir(config)
    db = Database(data_dir / "db.sqlite")
    repo = ProjectRepository(db)
    storage = ProjectStorage(data_dir)

    project = repo.get_by_name(project_name)
    if not project:
        print_error(f"Project '{project_name}' not found.")
        return False

    # Skip if already confirmed
    if project.status in (ProjectStatus.OUTLINE_CONFIRMED, ProjectStatus.GENERATING,
                          ProjectStatus.COMPLETED):
        print(f"  Outline already confirmed (status: {project.status.value})")
        choice = input_choice("Action?", [
            "Skip, keep existing outline",
            "Regenerate outline",
        ])
        if choice == 1:
            return True

    generator = DocumentGenerator(config, repo, storage)

    try:
        _ensure_design_brief(storage, project)
        while True:
            print("  Generating outline (calling LLM)...")
            try:
                outline_md = run_async(generator.generate_outline(project))
            except Exception as e:
                print_error(f"Outline generation failed: {type(e).__name__}: {e}")
                print("\n  Full error details:")
                traceback.print_exc()
                choice = input_choice("Action?", ["Retry", "Cancel"])
                if choice == 1:
                    continue
                return False

            print("\n" + "=" * 60)
            print(outline_md)
            print("=" * 60)

            action = prompt_outline_action()
            if action == "confirm":
                project.status = ProjectStatus.OUTLINE_CONFIRMED
                repo.update(project)
                print_success("Outline confirmed.")
                # Reload project to ensure status is persisted
                project = repo.get_by_name(project.name)
                return True
            elif action == "regenerate":
                print("  Regenerating...")
                continue
            else:
                print("  Outline generation cancelled.")
                return False
    except (KeyboardInterrupt, EOFError):
        print("\n  Outline generation cancelled.")
        return False
    finally:
        run_async(generator.close())


def step_generate_content(project_name: str) -> bool:
    """Generate all chapters."""
    from doc_gen.config.loader import ensure_data_dir, load_config
    from doc_gen.core.generator import DocumentGenerator
    from doc_gen.models.project import ProjectStatus
    from doc_gen.storage.database import Database
    from doc_gen.storage.project import ProjectStorage
    from doc_gen.storage.repository import ProjectRepository

    config = load_config()
    data_dir = ensure_data_dir(config)
    db = Database(data_dir / "db.sqlite")
    repo = ProjectRepository(db)
    storage = ProjectStorage(data_dir)

    project = repo.get_by_name(project_name)
    if not project:
        print_error(f"Project '{project_name}' not found.")
        return False

    if project.status == ProjectStatus.COMPLETED:
        print(f"  Content already generated.")
        choice = input_choice("Action?", [
            "Skip, keep existing content",
            "Regenerate all chapters",
        ])
        if choice == 1:
            return True

    if project.status not in (ProjectStatus.OUTLINE_CONFIRMED, ProjectStatus.COMPLETED):
        print_error("Outline not confirmed yet. Cannot generate content.")
        return False

    generator = DocumentGenerator(config, repo, storage)

    try:
        print("  Generating chapters (this may take a few minutes)...")
        try:
            chapter_files = run_async(generator.generate_content(project))
            print_success(f"{len(chapter_files)} chapters generated.")
            return True
        except Exception as e:
            print_error(f"Content generation failed: {type(e).__name__}: {e}")
            print("\n  Full error details:")
            traceback.print_exc()
            choice = input_choice("Action?", ["Retry", "Skip"])
            if choice == 1:
                try:
                    chapter_files = run_async(generator.generate_content(project))
                    print_success(f"{len(chapter_files)} chapters generated.")
                    return True
                except Exception as e2:
                    print_error(f"Retry failed: {type(e2).__name__}: {e2}")
                    traceback.print_exc()
                    return False
            return False
    except (KeyboardInterrupt, EOFError):
        print("\n  Content generation cancelled.")
        return False
    finally:
        run_async(generator.close())


def step_export(project_name: str) -> bool:
    """Export final document."""
    from doc_gen.config.loader import ensure_data_dir, load_config
    from doc_gen.core.generator import DocumentGenerator
    from doc_gen.storage.database import Database
    from doc_gen.storage.project import ProjectStorage
    from doc_gen.storage.repository import ProjectRepository

    config = load_config()
    data_dir = ensure_data_dir(config)
    db = Database(data_dir / "db.sqlite")
    repo = ProjectRepository(db)
    storage = ProjectStorage(data_dir)

    project = repo.get_by_name(project_name)
    if not project:
        print_error(f"Project '{project_name}' not found.")
        return False

    generator = DocumentGenerator(config, repo, storage)

    try:
        output_path = generator.export_document(project)
        print_success(f"Document exported to: {output_path}")
        return True
    except Exception as e:
        print_error(f"Export failed: {e}")
        return False


def main() -> None:
    print_header()

    # Step 0: Check .env
    if not check_env_file():
        input("\nPress Enter to exit...")
        return

    # Step 1: Check API
    print_step(1, 5, "Checking API connection")
    if not check_api_connection():
        print("\n  Please fix .env configuration and try again.")
        input("\nPress Enter to exit...")
        return

    # Step 2: Project name
    print_step(2, 5, "Project setup")
    project_name = input("  Project name: ").strip()
    if not project_name:
        print("  Project name is required.")
        input("\nPress Enter to exit...")
        return

    # Step 3: Create project
    if not step_create_project(project_name):
        input("\nPress Enter to exit...")
        return

    # Step 4: Generate outline
    print_step(3, 5, "Generating outline")
    if not step_generate_outline(project_name):
        print("\n  Workflow stopped at outline stage.")
        print(f"  You can resume later: python -m doc_gen generate {project_name} --stage outline")
        input("\nPress Enter to exit...")
        return

    # Step 5: Generate content
    print_step(4, 5, "Generating content")
    if not step_generate_content(project_name):
        print("\n  Workflow stopped at content stage.")
        print(f"  You can resume later: python -m doc_gen generate {project_name} --stage content")
        input("\nPress Enter to exit...")
        return

    # Step 6: Export
    print_step(5, 5, "Exporting document")
    step_export(project_name)

    print("\n" + "=" * 50)
    print("  Done! Check the output file above.")
    print("=" * 50)
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    try:
        main()
    finally:
        _loop.close()
