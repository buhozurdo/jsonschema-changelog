# jsonschema-changelog
Generador de changelogs y sugerencias de versionado semántico (semver) a partir del diff entre dos JSON Schema.

jsonschema-changelog compara dos versiones de un contrato (JSON Schema y, en un futuro, OpenAPI) y produce:
- Un changelog legible en Markdown con los cambios detectados.
- Una sugerencia de versión semver (patch/minor/major) basada en reglas heurísticas.
- Un reporte estructurado en JSON para pipelines o dashboards.

Estado: MVP en desarrollo. Alcance actual enfocado en: properties, required y tipos primarios.

---

## Características
- Diff entre dos JSON Schema:
  - Propiedades añadidas/eliminadas.
  - Cambios en `required`.
  - Cambios de tipo primario (`string`, `number`, `integer`, `boolean`, `array`, `object`).
- Sugerencia semver automática:
  - Cambios breaking → major.
  - Cambios adicionados compatibles → minor.
  - Correcciones no breaking → patch.
- Salida en Markdown y JSON.
- CLI simple y lista para CI (opción de fallar si hay cambios breaking).

Limitaciones actuales (MVP):
- No evalúa combinadores (`oneOf`, `anyOf`, `allOf`), `not`, ni `$ref` complejos.
- No analiza formatos (`format`), patrones (`pattern`) o rangos (`minimum`, `maxLength`, etc.).
- No comprende semántica específica de dominio; ofrece overrides por configuración.

---

## Requisitos
- Python 3.9 o superior (recomendado usar pipx para instalación aislada).

---

## Instalación
```bash
# Con pipx (recomendado)
pipx install jsonschema-changelog

# O con pip (en entorno virtual)
pip install jsonschema-changelog
```

---

## Uso rápido
```bash
# Generar changelog en Markdown y sugerencia semver
jsonschema-changelog schema-old.json schema-new.json \
  --format markdown \
  --semver-suggestion \
  --output CHANGELOG_SCHEMA.md

# Salida JSON para CI/pipelines
jsonschema-changelog schema-old.json schema-new.json \
  --format json \
  --semver-suggestion \
  --output report.json

# Fallar el proceso si hay cambios breaking (útil en PRs)
jsonschema-changelog schema-old.json schema-new.json --fail-on major
```

Opciones principales:
- `--format {markdown,json}`: formato de salida.
- `--output <ruta>`: archivo de salida (por defecto, imprime a stdout).
- `--semver-suggestion`: incluye `suggested_semver` en la salida.
- `--fail-on {patch,minor,major}`: salida con código ≠ 0 si el cambio mínimo detectado es ese nivel o superior.
- `--config <archivo>`: archivo de configuración para overrides/reglas.

Exit codes (para CI):
- 0: ejecución exitosa sin superar umbral de `--fail-on`.
- 1: se superó el umbral de `--fail-on` (p. ej., hay breaking y se usó `--fail-on major`).
- 2: error de uso/parseo.

---

## Ejemplo

Schemas de ejemplo:
```json
// schema-v1.json
{
  "type": "object",
  "properties": {
    "id": { "type": "string" },
    "age": { "type": "integer" }
  },
  "required": ["id"]
}
```

```json
// schema-v2.json
{
  "type": "object",
  "properties": {
    "id": { "type": "string" },
    "age": { "type": "number" },
    "email": { "type": "string" }
  },
  "required": ["id", "email"]
}
```

Comando:
```bash
jsonschema-changelog schema-v1.json schema-v2.json --format markdown --semver-suggestion
```

Salida (Markdown):
```markdown
## JSON Schema Changelog

Sugerencia semver: major

Cambios detectados:
- Added property: email
- Required changed: property 'email' is now required
- Type changed: property 'age' from integer to number
```

Salida (JSON):
```json
{
  "suggested_semver": "major",
  "changes": [
    {
      "kind": "property_added",
      "path": "properties.email",
      "breaking": false,
      "details": { "type": "string" }
    },
    {
      "kind": "required_added",
      "path": "required.email",
      "breaking": true,
      "details": { "property": "email" }
    },
    {
      "kind": "type_changed",
      "path": "properties.age",
      "breaking": "maybe",
      "details": { "from": "integer", "to": "number" }
    }
  ],
  "summary": {
    "added": 1,
    "removed": 0,
    "required_added": 1,
    "required_removed": 0,
    "type_changed": 1,
    "breaking_changes": 1
  }
}
```

Nota: algunos cambios de tipo pueden ser “quizá breaking” según el contexto. Puedes forzar su interpretación con configuración.

---

## Reglas de sugerencia semver (MVP)
Heurística por defecto:
- major (rompiente):
  - Eliminación de propiedad existente.
  - Añadir una propiedad a `required`.
  - Cambio de tipo no compatible (p. ej., `string` → `number`, `object` → `array`).
- minor (compatible):
  - Añadir propiedad opcional.
- patch:
  - Cambios no estructurales (metadatos) o sin impacto detectado.

Overrides:
- Puedes declarar excepciones por ruta de propiedad (p. ej., considerar `integer` → `number` como no-breaking en tu dominio).

---

## Configuración (opcional)
Archivo YAML/JSON de configuración para ajustar reglas y excepciones.

```yaml
# jsonschema-changelog.yml
rules:
  # Forzar interpretación de cambios de tipo
  type_change_overrides:
    - path: "properties.age"
      from: "integer"
      to: "number"
      breaking: false
  # Tratar propiedades bajo un prefijo como experimentales (no-breaking al eliminar)
  experimental_paths:
    - "properties.experimental_.*"  # regex

# Niveles mínimos por tipo de cambio (major/minor/patch)
severity:
  property_removed: major
  property_added_optional: minor
  required_added: major
  required_removed: major
  type_changed_default: major
```

Uso:
```bash
jsonschema-changelog schema-old.json schema-new.json --config jsonschema-changelog.yml
```

---

## Integración con CI (GitHub Actions)

Ejemplo sencillo usando pipx:
```yaml
# .github/workflows/schema-diff.yml
name: Schema Diff

on:
  pull_request:
    paths:
      - "schemas/**.json"

jobs:
  diff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install jsonschema-changelog
        run: |
          pipx install jsonschema-changelog
      - name: Run diff and generate report
        run: |
          jsonschema-changelog schemas/schema-v1.json schemas/schema-v2.json \
            --format markdown --semver-suggestion --output changelog.md || echo "Diff generated"
      - name: Comment changelog on PR
        uses: marocchino/sticky-pull-request-comment@v2
        with:
          path: changelog.md
```

Bloquear merges si hay breaking:
```yaml
- name: Fail on breaking changes
  run: |
    jsonschema-changelog schemas/schema-v1.json schemas/schema-v2.json --fail-on major
```

---

## API de salida JSON (MVP)
Estructura orientativa:
```json
{
  "suggested_semver": "major|minor|patch",
  "changes": [
    {
      "kind": "property_added|property_removed|required_added|required_removed|type_changed",
      "path": "properties.user.name",
      "breaking": true,
      "details": {}
    }
  ],
  "summary": {
    "added": 0,
    "removed": 0,
    "required_added": 0,
    "required_removed": 0,
    "type_changed": 0,
    "breaking_changes": 0
  }
}
```

---

## Buenas prácticas
- Versiona tus schemas junto al código o en un repo dedicado.
- Usa el reporte JSON para dashboards de compatibilidad.
- Añade reglas de override para casos de dominio que no sean universalmente breaking.

---

## Roadmap
- Soporte para combinadores (`oneOf`, `anyOf`, `allOf`) y `$ref`.
- Integración con OpenAPI (components/schemas).
- Reglas de compatibilidad más ricas (rangos, `enum`, `format`, `pattern`).
- Comentario automático en PR con sugerencia de bump y notas de migración.
- Plugins de “reglas de dominio” y perfiles predefinidos.

---

## Contribuir
¡Contribuciones bienvenidas!
- Abre un issue con propuesta/bug.
- Envía un PR con tests.
- Estilo de código: black + isort + flake8.
- Tests: pytest.

Pasos de desarrollo:
```bash
git clone https://github.com/tu-org/jsonschema-changelog
cd jsonschema-changelog
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

---

## Seguridad
Este proyecto no procesa datos sensibles, pero puede formar parte de tus pipelines de release. Revisa cuidadosamente reglas y overrides antes de automatizar fallos de CI.

Reporta vulnerabilidades por canales privados (SECURITY.md).

---

## Licencia
MIT. Consulta LICENSE para más detalles.

---

## FAQ
- ¿Funciona con OpenAPI? No en el MVP. Está en el roadmap mediante el análisis de `components.schemas`.
- ¿Puede entender `$ref`? Parcialmente/no en MVP. Se recomienda resolver refs antes del diff o aceptar la limitación.
- ¿Por qué sugiere major tan a menudo? Las reglas son conservadoras por defecto. Ajusta overrides en `--config`.
