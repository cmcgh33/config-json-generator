"""In-memory workbook processing shared by the interface and its tests."""
from io import BytesIO
import json
from zipfile import BadZipFile, ZipFile

from .excel_importer import load_input
from .generator import generate, ValidationError
from .validate_config import validate_config

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_EXPANDED_BYTES = 20 * 1024 * 1024


class WorkbookError(ValueError):
    """A workbook cannot produce a validated downloadable configuration."""


def compile_workbook(content):
    """Return validated JSON and its download text without writing uploaded files."""
    if not content:
        raise WorkbookError('Choose an Excel workbook before generating.')
    if len(content) > MAX_UPLOAD_BYTES:
        raise WorkbookError('Workbook exceeds the 5 MB upload limit.')
    try:
        with ZipFile(BytesIO(content)) as archive:
            if len(archive.infolist()) > 300 or sum(item.file_size for item in archive.infolist()) > MAX_EXPANDED_BYTES:
                raise WorkbookError('Workbook is too large when expanded. Use the input template with up to 1,000 data rows per table.')
            names = archive.namelist()
            if '[Content_Types].xml' not in names or 'xl/workbook.xml' not in names:
                raise WorkbookError('This file is not an Excel workbook. Download the template and save it as .xlsx.')
        config = generate(load_input(BytesIO(content)))
        errors = validate_config(config)
        if errors:
            raise WorkbookError('\n'.join(errors))
        payload = json.dumps(config, indent=2, allow_nan=False) + '\n'
        return {'config': config, 'payload': payload,
                'filename': f'{config["model"]["id"]}_config.json'}
    except WorkbookError:
        raise
    except (ValidationError, ValueError, OSError, BadZipFile, KeyError, SyntaxError, OverflowError) as exc:
        raise WorkbookError(f'Workbook could not be processed: {exc}') from exc
