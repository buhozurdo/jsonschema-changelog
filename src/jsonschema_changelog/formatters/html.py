"""HTML formatter for changelogs."""

from typing import Any, List

from jinja2 import Template

from jsonschema_changelog.changelog import Changelog, VersionEntry
from jsonschema_changelog.classifier import ChangeCategory

# Default HTML template
DEFAULT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ changelog.title }}</title>
    <style>
        :root {
            --color-breaking: #dc3545;
            --color-deprecation: #ffc107;
            --color-non-breaking: #28a745;
            --color-documentation: #17a2b8;
            --color-bg: #ffffff;
            --color-text: #333333;
            --color-border: #dee2e6;
        }
        
        @media (prefers-color-scheme: dark) {
            :root {
                --color-bg: #1a1a2e;
                --color-text: #eaeaea;
                --color-border: #3d3d5c;
            }
        }
        
        * {
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: var(--color-text);
            background-color: var(--color-bg);
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        h1 {
            border-bottom: 2px solid var(--color-border);
            padding-bottom: 0.5rem;
        }
        
        h2 {
            margin-top: 2rem;
            padding-bottom: 0.3rem;
            border-bottom: 1px solid var(--color-border);
        }
        
        .version-entry {
            margin-bottom: 3rem;
        }
        
        .badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            font-size: 0.75rem;
            font-weight: bold;
            border-radius: 4px;
            margin-left: 0.5rem;
        }
        
        .badge-breaking {
            background-color: var(--color-breaking);
            color: white;
        }
        
        .badge-deprecation {
            background-color: var(--color-deprecation);
            color: black;
        }
        
        .badge-non-breaking {
            background-color: var(--color-non-breaking);
            color: white;
        }
        
        .badge-documentation {
            background-color: var(--color-documentation);
            color: white;
        }
        
        .metadata {
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
        
        .summary-table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }
        
        .summary-table th,
        .summary-table td {
            padding: 0.5rem;
            text-align: left;
            border: 1px solid var(--color-border);
        }
        
        .summary-table th {
            background-color: rgba(0,0,0,0.05);
        }
        
        .change-section {
            margin: 1.5rem 0;
        }
        
        .change-section h3 {
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }
        
        .change-item {
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 4px;
            border-left: 4px solid var(--color-border);
            background-color: rgba(0,0,0,0.02);
        }
        
        .change-item.breaking {
            border-left-color: var(--color-breaking);
        }
        
        .change-item.deprecation {
            border-left-color: var(--color-deprecation);
        }
        
        .change-item.non-breaking {
            border-left-color: var(--color-non-breaking);
        }
        
        .change-item.documentation {
            border-left-color: var(--color-documentation);
        }
        
        .change-path {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.85rem;
            background-color: rgba(0,0,0,0.05);
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
        }
        
        .change-impact {
            margin-top: 0.5rem;
            font-size: 0.9rem;
            color: #666;
        }
        
        .migration-hint {
            margin-top: 0.5rem;
            padding: 0.5rem;
            background-color: rgba(255, 193, 7, 0.1);
            border-radius: 4px;
            font-size: 0.9rem;
        }
        
        .migration-hint::before {
            content: "🛠️ ";
        }
        
        .value-change {
            margin-top: 0.5rem;
            font-size: 0.9rem;
        }
        
        .value-old {
            text-decoration: line-through;
            color: var(--color-breaking);
        }
        
        .value-new {
            color: var(--color-non-breaking);
        }
        
        footer {
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid var(--color-border);
            font-size: 0.8rem;
            color: #666;
            text-align: center;
        }
    </style>
</head>
<body>
    <header>
        <h1>{{ changelog.title }}</h1>
        {% if changelog.description %}
        <p>{{ changelog.description }}</p>
        {% endif %}
    </header>
    
    <main>
        {% for entry in changelog.entries %}
        <article class="version-entry" id="version-{{ entry.version | replace('.', '-') }}">
            <h2>
                {{ entry.version }}
                {% if entry.is_breaking %}
                <span class="badge badge-breaking">🚨 BREAKING</span>
                {% endif %}
            </h2>
            
            <div class="metadata">
                <strong>Date:</strong> {{ entry.date }} |
                <strong>Previous:</strong> {{ entry.previous_version }}
            </div>
            
            {% if include_summary %}
            <table class="summary-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Count</th>
                    </tr>
                </thead>
                <tbody>
                    {% if entry.summary.breaking > 0 %}
                    <tr>
                        <td>🚨 Breaking</td>
                        <td>{{ entry.summary.breaking }}</td>
                    </tr>
                    {% endif %}
                    {% if entry.summary.deprecation > 0 %}
                    <tr>
                        <td>⚠️ Deprecations</td>
                        <td>{{ entry.summary.deprecation }}</td>
                    </tr>
                    {% endif %}
                    {% if entry.summary.non_breaking > 0 %}
                    <tr>
                        <td>✨ Non-breaking</td>
                        <td>{{ entry.summary.non_breaking }}</td>
                    </tr>
                    {% endif %}
                    {% if entry.summary.documentation > 0 %}
                    <tr>
                        <td>📝 Documentation</td>
                        <td>{{ entry.summary.documentation }}</td>
                    </tr>
                    {% endif %}
                    <tr>
                        <th>Total</th>
                        <th>{{ entry.summary.total }}</th>
                    </tr>
                </tbody>
            </table>
            {% endif %}
            
            {% if entry.breaking_changes %}
            <section class="change-section">
                <h3>🚨 Breaking Changes</h3>
                {% for change in entry.breaking_changes %}
                {{ render_change(change, 'breaking') }}
                {% endfor %}
            </section>
            {% endif %}
            
            {% if entry.deprecations %}
            <section class="change-section">
                <h3>⚠️ Deprecations</h3>
                {% for change in entry.deprecations %}
                {{ render_change(change, 'deprecation') }}
                {% endfor %}
            </section>
            {% endif %}
            
            {% if entry.non_breaking_changes %}
            <section class="change-section">
                <h3>✨ Changes</h3>
                {% for change in entry.non_breaking_changes %}
                {{ render_change(change, 'non-breaking') }}
                {% endfor %}
            </section>
            {% endif %}
            
            {% if entry.documentation_changes %}
            <section class="change-section">
                <h3>📝 Documentation</h3>
                {% for change in entry.documentation_changes %}
                {{ render_change(change, 'documentation') }}
                {% endfor %}
            </section>
            {% endif %}
        </article>
        {% endfor %}
    </main>
    
    <footer>
        <p>Generated by <strong>jsonschema-changelog</strong> | Part of the Búho Zurdo ecosystem</p>
    </footer>
</body>
</html>
"""


class HtmlFormatter:
    """Format changelog as HTML.

    Generates a styled HTML page with the changelog content.
    Uses Jinja2 for templating.

    Example:
        >>> formatter = HtmlFormatter()
        >>> html = formatter.format(changelog)
    """

    def __init__(
        self,
        template: str = None,
        include_summary: bool = True,
        show_migration_hints: bool = True,
    ) -> None:
        """Initialize HtmlFormatter.

        Args:
            template: Custom Jinja2 template (uses default if None)
            include_summary: Include change summary table
            show_migration_hints: Show migration hints for breaking changes
        """
        self.template = template or DEFAULT_TEMPLATE
        self.include_summary = include_summary
        self.show_migration_hints = show_migration_hints

    def format(self, changelog: Changelog) -> str:
        """Format a changelog as HTML.

        Args:
            changelog: The changelog to format

        Returns:
            HTML formatted string
        """
        template = Template(self.template)

        return template.render(
            changelog=changelog,
            include_summary=self.include_summary,
            show_migration_hints=self.show_migration_hints,
            render_change=self._render_change,
        )

    def _render_change(self, classified_change: Any, category_class: str) -> str:
        """Render a single change as HTML."""
        change = classified_change.change

        html_parts = [
            f'<div class="change-item {category_class}">',
            f'<strong>{self._escape(change.description)}</strong>',
            f'<div>Path: <code class="change-path">{self._escape(change.path)}</code></div>',
            f'<div class="change-impact">{self._escape(classified_change.impact_description)}</div>',
        ]

        # Migration hint
        if (
            self.show_migration_hints
            and classified_change.category == ChangeCategory.BREAKING
            and classified_change.migration_hint
        ):
            html_parts.append(
                f'<div class="migration-hint">{self._escape(classified_change.migration_hint)}</div>'
            )

        # Value changes
        if change.old_value is not None or change.new_value is not None:
            value_html = '<div class="value-change">'
            if change.old_value is not None and change.new_value is not None:
                value_html += f'<span class="value-old">{self._escape(str(change.old_value))}</span> → '
                value_html += f'<span class="value-new">{self._escape(str(change.new_value))}</span>'
            elif change.old_value is not None:
                value_html += f'Removed: <span class="value-old">{self._escape(str(change.old_value))}</span>'
            else:
                value_html += f'Added: <span class="value-new">{self._escape(str(change.new_value))}</span>'
            value_html += '</div>'
            html_parts.append(value_html)

        html_parts.append('</div>')

        return "\n".join(html_parts)

    def _escape(self, text: str) -> str:
        """Escape HTML special characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )
