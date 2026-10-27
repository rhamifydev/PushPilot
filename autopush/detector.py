"""
Language, Framework, and Stack Detection for Autopush.
Detects project stacks, component types, and supplies tailored .gitignore templates.
"""

import json
from pathlib import Path
from typing import NamedTuple


class ProjectStack(NamedTuple):
    language: str
    framework: str | None
    ecosystem: str
    build_tool: str | None


class StackDetector:
    """Detects programming languages, frameworks, and architecture patterns."""

    @classmethod
    def detect(cls, root: Path) -> ProjectStack:
        # Check Node.js / TypeScript / JavaScript
        pkg_json = root / "package.json"
        if pkg_json.is_file():
            try:
                with open(pkg_json, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
                deps = {
                    **data.get("dependencies", {}),
                    **data.get("devDependencies", {}),
                }

                framework = None
                if "next" in deps:
                    framework = "Next.js"
                elif "react" in deps and "react-native" in deps:
                    framework = "React Native"
                elif "react" in deps:
                    framework = "React"
                elif "vue" in deps or "nuxt" in deps:
                    framework = "Nuxt.js" if "nuxt" in deps else "Vue.js"
                elif "@angular/core" in deps:
                    framework = "Angular"
                elif "svelte" in deps or "@sveltejs/kit" in deps:
                    framework = "Svelte"
                elif "@nestjs/core" in deps:
                    framework = "NestJS"
                elif "express" in deps:
                    framework = "Express.js"
                elif "vite" in deps:
                    framework = "Vite App"

                is_ts = any(root.glob("tsconfig*.json")) or "typescript" in deps
                lang = "TypeScript" if is_ts else "JavaScript"
                return ProjectStack(
                    language=lang,
                    framework=framework or "Node.js",
                    ecosystem="npm/node",
                    build_tool="npm" if not (root / "yarn.lock").exists() else "yarn",
                )
            except Exception:
                pass

        # Check Python
        py_files = list(root.glob("*.py"))
        req_txt = root / "requirements.txt"
        pyproject = root / "pyproject.toml"
        pipfile = root / "Pipfile"

        if py_files or req_txt.exists() or pyproject.exists() or pipfile.exists():
            framework = None
            # Check for Django
            if (root / "manage.py").exists() or any(root.glob("*/settings.py")):
                framework = "Django"
            else:
                # Check requirements or imports
                req_content = ""
                if req_txt.is_file():
                    req_content += req_txt.read_text(encoding="utf-8", errors="ignore")
                if pyproject.is_file():
                    req_content += pyproject.read_text(encoding="utf-8", errors="ignore")

                req_lower = req_content.lower()
                if "fastapi" in req_lower:
                    framework = "FastAPI"
                elif "flask" in req_lower:
                    framework = "Flask"
                elif "torch" in req_lower or "tensorflow" in req_lower:
                    framework = "AI/Machine Learning"

            return ProjectStack(
                language="Python",
                framework=framework or "Standard Python",
                ecosystem="pip/python",
                build_tool="poetry" if (root / "poetry.lock").exists() else "pip",
            )

        # Check Rust
        if (root / "Cargo.toml").exists():
            return ProjectStack(
                language="Rust",
                framework="Cargo App",
                ecosystem="cargo",
                build_tool="cargo",
            )

        # Check Go
        if (root / "go.mod").exists() or list(root.glob("*.go")):
            return ProjectStack(
                language="Go",
                framework="Go Module",
                ecosystem="go",
                build_tool="go",
            )

        # Check Flutter / Dart
        if (root / "pubspec.yaml").exists():
            content = (root / "pubspec.yaml").read_text(encoding="utf-8", errors="ignore")
            is_flutter = "flutter:" in content
            return ProjectStack(
                language="Dart",
                framework="Flutter" if is_flutter else "Dart Console",
                ecosystem="pub",
                build_tool="flutter" if is_flutter else "dart",
            )

        # Check Java / Kotlin
        if (root / "pom.xml").exists():
            return ProjectStack(
                language="Java",
                framework="Maven Project",
                ecosystem="maven",
                build_tool="mvn",
            )
        if (root / "build.gradle").exists() or (root / "build.gradle.kts").exists():
            is_kotlin = (root / "build.gradle.kts").exists()
            return ProjectStack(
                language="Kotlin" if is_kotlin else "Java",
                framework="Gradle Project",
                ecosystem="gradle",
                build_tool="gradle",
            )

        # Check C# / .NET
        if list(root.glob("*.csproj")) or list(root.glob("*.sln")):
            return ProjectStack(
                language="C#",
                framework=".NET Core / C#",
                ecosystem="dotnet",
                build_tool="dotnet",
            )

        # Check PHP
        if (root / "composer.json").exists() or list(root.glob("*.php")):
            framework = "Laravel" if (root / "artisan").exists() else "PHP App"
            return ProjectStack(
                language="PHP",
                framework=framework,
                ecosystem="composer",
                build_tool="composer",
            )

        # Check Ruby
        if (root / "Gemfile").exists():
            framework = "Ruby on Rails" if (root / "bin" / "rails").exists() else "Ruby App"
            return ProjectStack(
                language="Ruby",
                framework=framework,
                ecosystem="rubygems",
                build_tool="bundle",
            )

        # Default fallback
        return ProjectStack(
            language="Universal",
            framework="Generic Project",
            ecosystem="git",
            build_tool=None,
        )

    @classmethod
    def get_recommended_gitignore(cls, stack: ProjectStack) -> str:
        """Returns recommended .gitignore rules tailored to the detected language and framework."""
        common = """# OS & Editor temp files
.DS_Store
Thumbs.db
*.swp
*.bak
.idea/
.vscode/
*.log
.env
.env.local
.env.*.local
"""
        lang = stack.language.lower()
        if "python" in lang:
            return common + """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.venv/
env/
venv/
ENV/
build/
dist/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/
"""
        elif "javascript" in lang or "typescript" in lang or "node" in lang:
            return common + """
# Node & Web
node_modules/
dist/
build/
.next/
out/
.nuxt/
.svelte-kit/
.turbo/
coverage/
*.tsbuildinfo
"""
        elif "rust" in lang:
            return common + """
# Rust
target/
**/*.rs.bk
Cargo.lock
"""
        elif "go" in lang:
            return common + """
# Go
bin/
pkg/
*.exe
*.test
vendor/
"""
        elif "dart" in lang:
            return common + """
# Flutter & Dart
.dart_tool/
.packages
build/
.flutter-plugins
.flutter-plugins-dependencies
"""
        elif "java" in lang or "kotlin" in lang:
            return common + """
# Java & Gradle / Maven
target/
build/
.gradle/
*.class
*.jar
*.war
"""
        elif "c#" in lang:
            return common + """
# .NET
bin/
obj/
*.user
*.suo
"""
        elif "php" in lang:
            return common + """
# PHP & Composer
vendor/
composer.phar
.phpunit.result.cache
"""
        return common


def classify_file_role(filepath: str) -> tuple[str, str]:
    """Classifies a changed file into (category, component_name).
    Returns category (e.g. 'ui', 'api', 'model', 'auth', 'test', 'docs', 'config')
    and a clean component label.
    """
    path_obj = Path(filepath)
    filename = path_obj.name.lower()
    parts = [p.lower() for p in path_obj.parts]

    # Documentation
    if filename.endswith((".md", ".txt", ".rst")) or "doc" in parts or "docs" in parts:
        return "docs", "documentation"

    # Tests
    if (
        "test" in filename
        or "spec" in filename
        or "tests" in parts
        or "test" in parts
        or "__tests__" in parts
    ):
        stem = path_obj.stem.replace(".test", "").replace(".spec", "").replace("test_", "")
        return "test", stem

    # Configuration / Dependencies / Pipelines
    if filename in (
        "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
        "requirements.txt", "pyproject.toml", "pipfile", "pipfile.lock",
        "cargo.toml", "cargo.lock", "go.mod", "go.sum", "pom.xml",
        "build.gradle", "build.gradle.kts", "composer.json", "gemfile",
        "dockerfile", "docker-compose.yml", "docker-compose.yaml",
        ".gitignore", "tsconfig.json", "vite.config.ts", "vite.config.js"
    ) or ".github" in parts:
        return "config", path_obj.stem

    # Frontend Layouts & Wrappers (must not be treated as auth workflow)
    if "layout" in filename or "layouts" in parts:
        return "ui", "layout"

    # Frontend Pages, Components & Views
    if any(k in filename or k in parts for k in ("component", "components", "pages", "views", "screens", "widgets", "templates")):
        # Extract meaningful feature folder if inside Pages or Components
        feature_name = path_obj.stem
        skip_dirs = {
            "pages", "components", "resources", "js", "ts", "jsx", "tsx", "src", "views",
            "partials", "partial", "shared", "common", "elements", "widgets", "layout", "layouts",
            "base", "subviews", "fragments", "templates", "ui", "app"
        }
        for p in reversed(parts[:-1]):
            if p.lower() not in skip_dirs:
                feature_name = p
                break
        return "ui", feature_name

    # API / Controllers / Routes / Endpoints
    if any(k in filename or k in parts for k in ("api", "route", "routes", "controller", "controllers", "endpoint", "handler", "viewset", "rpc")):
        stem = path_obj.stem.replace("Controller", "").replace("Handler", "")
        return "api", stem or path_obj.stem

    # Database / Models / Schemas / Migrations
    if any(k in filename or k in parts for k in ("model", "models", "schema", "schemas", "entity", "entities", "migration", "migrations", "db")):
        stem = path_obj.stem.replace("Model", "")
        return "model", stem or path_obj.stem

    # Authentication & Security (strict: genuine auth services/endpoints)
    if any(k in filename for k in ("login", "register", "oauth", "password", "jwt", "session_guard", "two_factor")) or (
        ("auth" in parts or "auth" in filename) and not ("layout" in filename or "author" in filename)
    ):
        return "auth", path_obj.stem

    # Styling & Visual
    if filename.endswith((".css", ".scss", ".sass", ".less", ".tailwind")):
        return "style", path_obj.stem

    # Services / Utils / Helpers
    if any(k in filename or k in parts for k in ("service", "services", "util", "utils", "helper", "helpers", "lib")):
        return "service", path_obj.stem

    return "core", path_obj.stem
