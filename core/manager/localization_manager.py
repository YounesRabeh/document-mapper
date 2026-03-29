from __future__ import annotations

import re

from PySide6.QtCore import QObject, QSettings, Signal


TRANSLATIONS = {
    "en": {
        "app.name": "Document Mapper",
        "menu.file": "File",
        "menu.view": "View",
        "menu.help": "Help",
        "menu.language": "Language",
        "menu.language.en": "English",
        "menu.language.it": "Italiano",
        "sidebar.heading": "Workflow",
        "sidebar.subtitle": "Configure, map, generate, and review each certificate batch.",
        "sidebar.stage.setup": "Setup",
        "sidebar.stage.setup.detail": "Files, template, and export options",
        "sidebar.stage.mapping": "Mapping",
        "sidebar.stage.mapping.detail": "Placeholders and workbook columns",
        "sidebar.stage.generate": "Generate",
        "sidebar.stage.generate.detail": "Run the batch and follow progress",
        "sidebar.stage.results": "Results",
        "sidebar.stage.results.detail": "Open files and review output",
        "action.new_project": "New Project",
        "action.open_project": "Open Project...",
        "action.save_project": "Save Project",
        "action.save_project_as": "Save Project As...",
        "action.exit": "Exit",
        "action.toggle_theme": "Toggle Theme",
        "action.about": "About",
        "dialog.open_project.title": "Open project",
        "dialog.open_project.failed_title": "Open project failed",
        "dialog.save_project.title": "Save project",
        "dialog.project_files": "Project Files (*.json)",
        "dialog.select_excel_workbook.title": "Select Excel workbook",
        "dialog.excel_files": "Excel Files (*.xlsx *.xls)",
        "dialog.select_word_template.title": "Select Word template",
        "dialog.word_files": "Word Files (*.docx *.doc)",
        "dialog.select_output_folder.title": "Select output folder",
        "dialog.about.title": "About Document Mapper",
        "dialog.about.body": "Document Mapper creates DOCX certificates from Excel data and optional PDF exports.",
        "dialog.cannot_continue.title": "Cannot continue",
        "dialog.cannot_generate.title": "Cannot generate",
        "dialog.generation_failed.title": "Generation failed",
        "common.not_selected": "Not selected",
        "common.yes": "Yes",
        "common.no": "No",
        "page.setup.title": "Setup",
        "page.setup.description": "Choose the Excel workbook, Word template, output folder, and generation options for this certificate batch.",
        "card.certificate_batch": "Certificate Batch",
        "field.excel_workbook": "Excel workbook",
        "field.word_template": "Word template",
        "field.output_folder": "Output folder",
        "field.certificate_type": "Certificate type",
        "field.pdf_timeout": "PDF timeout",
        "placeholder.select_excel_workbook": "Select Excel workbook",
        "placeholder.select_word_template": "Select Word template",
        "placeholder.select_output_folder": "Select output folder",
        "button.workbook": "Workbook",
        "button.template": "Template",
        "button.output_folder": "Output folder",
        "hint.certificate_type": "Integrale: tipo B/C = 12 ore, tipo A = 16 ore. Retraining: tipo B/C = 4h, tipo A = 6h.",
        "card.export_options": "Export Options",
        "checkbox.export_pdf": "Also export PDF",
        "card.session_summary": "Session Summary",
        "button.next_mapping": "Next: Mapping",
        "summary.workbook": "Workbook: {value}",
        "summary.template": "Template: {value}",
        "summary.output_folder": "Output folder: {value}",
        "summary.certificate_type": "Certificate type: {value}",
        "summary.mappings_configured": "Mappings configured: {count}",
        "page.mapping.title": "Mapping",
        "page.mapping.description": "Create explicit mappings between the literal placeholders used in the template and the columns available in the workbook.",
        "group.workbook_columns": "Workbook columns",
        "status.no_workbook_loaded": "No workbook loaded yet.",
        "status.select_workbook_for_columns": "Select a workbook on the Setup page to see available columns.",
        "status.could_not_inspect_workbook": "Could not inspect workbook: {error}",
        "status.rows_detected": "{row_count} rows detected in {path}",
        "hint.columns_panel": "Double-click a column to create a mapping row quickly, or select one and use the button below.",
        "group.placeholder_mappings": "Placeholder mappings",
        "hint.mapping_editor": "Use the exact placeholder text from the Word template, for example <<NOME>>.",
        "status.select_template_for_placeholders": "Select a Word template to detect placeholders like <<NOME>>.",
        "status.detected_template_placeholders": "Detected {count} placeholders",
        "status.no_template_placeholders_detected": "No <...> placeholders were detected in the selected template.",
        "status.could_not_inspect_template": "Could not inspect template placeholders: {error}",
        "table.placeholder": "Placeholder",
        "table.excel_column": "Excel column",
        "button.add_mapping": "Add mapping",
        "button.remove_selected": "Remove selected",
        "button.refresh_mapping_data": "Refresh",
        "button.use_selected_column": "Use selected column",
        "label.validation": "Validation",
        "status.ready_to_generate": "Ready to generate certificates.",
        "status.validation_issues": "{count} items to fix before continuing.",
        "status.validation_ready_detail": "Everything looks good. You can continue to generation.",
        "button.back": "Back",
        "button.next_generate": "Next: Generate",
        "page.generate.title": "Generate",
        "page.generate.description": "Review the current batch, validate the inputs, and run the document generation pipeline.",
        "group.batch_summary": "Batch summary",
        "group.generation_log": "Generation log",
        "button.generate_certificates": "Generate certificates",
        "summary.output": "Output: {value}",
        "summary.mappings": "Mappings: {count}",
        "summary.export_pdf_enabled": "Export PDF: {value}",
        "summary.validation": "Validation",
        "summary.ready_to_generate_short": "- Ready to generate",
        "log.generation_finished": "Generation finished.",
        "log.generation_failed": "Generation failed: {error}",
        "page.results.title": "Results",
        "page.results.description": "Review the output from the last run, open the generated files, and inspect any generation errors.",
        "status.no_generation_results": "No generation results yet.",
        "group.generated_files": "Generated files",
        "group.errors": "Errors",
        "button.open_output_folder": "Open output folder",
        "button.open_log": "Open log",
        "results.created_docx": "Created {success_count} of {total_rows} DOCX certificates.",
        "results.generated_pdfs": "Generated PDFs: {count}",
        "results.files_listed": "Files listed: {count}",
        "results.last_certificate_number": "Last certificate number: {value}",
        "results.log_file": "Log file: {path}",
        "results.no_generation_errors": "No generation errors.",
        "runtime.select_excel_workbook": "Select an Excel workbook.",
        "runtime.excel_file_not_found": "Excel file not found: {path}",
        "runtime.select_word_template": "Select a Word certificate template.",
        "runtime.template_file_not_found": "Template file not found: {path}",
        "runtime.choose_output_folder": "Choose an output folder.",
        "runtime.output_not_writable": "Output folder is not writable: {error}",
        "runtime.license_file_not_found": "License file not found: {path}",
        "runtime.add_placeholder_mapping": "Add at least one placeholder mapping.",
        "runtime.cannot_read_excel": "Cannot read Excel workbook: {error}",
        "runtime.mapping_missing_placeholder": "Mapping row {row} is missing a placeholder.",
        "runtime.placeholder_duplicate": "Placeholder '{placeholder}' is mapped more than once.",
        "runtime.mapping_missing_column": "Mapping row {row} is missing an Excel column.",
        "runtime.column_not_available": "Excel column '{column}' is not available in the selected workbook.",
        "runtime.failed_generate_row": "Failed to generate row {row}: {error}",
        "runtime.spire_not_installed": "Spire.Doc is not installed. Install the runtime dependency before generating certificates.",
    },
    "it": {
        "app.name": "Document Mapper",
        "menu.file": "File",
        "menu.view": "Visualizza",
        "menu.help": "Aiuto",
        "menu.language": "Lingua",
        "menu.language.en": "English",
        "menu.language.it": "Italiano",
        "sidebar.heading": "Workflow",
        "sidebar.subtitle": "Configura, mappa, genera e controlla ogni batch di certificati.",
        "sidebar.stage.setup": "Configurazione",
        "sidebar.stage.setup.detail": "File, modello e opzioni di esportazione",
        "sidebar.stage.mapping": "Mappatura",
        "sidebar.stage.mapping.detail": "Segnaposto e colonne del file Excel",
        "sidebar.stage.generate": "Generazione",
        "sidebar.stage.generate.detail": "Esegui il batch e segui il progresso",
        "sidebar.stage.results": "Risultati",
        "sidebar.stage.results.detail": "Apri i file e controlla l'output",
        "action.new_project": "Nuovo progetto",
        "action.open_project": "Apri progetto...",
        "action.save_project": "Salva progetto",
        "action.save_project_as": "Salva progetto come...",
        "action.exit": "Esci",
        "action.toggle_theme": "Cambia tema",
        "action.about": "Informazioni",
        "dialog.open_project.title": "Apri progetto",
        "dialog.open_project.failed_title": "Apertura progetto non riuscita",
        "dialog.save_project.title": "Salva progetto",
        "dialog.project_files": "File progetto (*.json)",
        "dialog.select_excel_workbook.title": "Seleziona file Excel",
        "dialog.excel_files": "File Excel (*.xlsx *.xls)",
        "dialog.select_word_template.title": "Seleziona modello Word",
        "dialog.word_files": "File Word (*.docx *.doc)",
        "dialog.select_output_folder.title": "Seleziona cartella output",
        "dialog.about.title": "Informazioni su Document Mapper",
        "dialog.about.body": "Document Mapper crea certificati DOCX a partire da dati Excel con esportazione PDF opzionale.",
        "dialog.cannot_continue.title": "Impossibile continuare",
        "dialog.cannot_generate.title": "Impossibile generare",
        "dialog.generation_failed.title": "Generazione non riuscita",
        "common.not_selected": "Non selezionato",
        "common.yes": "Sì",
        "common.no": "No",
        "page.setup.title": "Configurazione",
        "page.setup.description": "Scegli il file Excel, il modello Word, la cartella di output e le opzioni di generazione per questo batch di certificati.",
        "card.certificate_batch": "Batch certificati",
        "field.excel_workbook": "File Excel",
        "field.word_template": "Modello Word",
        "field.output_folder": "Cartella output",
        "field.certificate_type": "Tipo certificato",
        "field.pdf_timeout": "Timeout PDF",
        "placeholder.select_excel_workbook": "Seleziona file Excel",
        "placeholder.select_word_template": "Seleziona modello Word",
        "placeholder.select_output_folder": "Seleziona cartella output",
        "button.workbook": "File Excel",
        "button.template": "Modello",
        "button.output_folder": "Cartella output",
        "hint.certificate_type": "Integrale: tipo B/C = 12 ore, tipo A = 16 ore. Retraining: tipo B/C = 4h, tipo A = 6h.",
        "card.export_options": "Opzioni esportazione",
        "checkbox.export_pdf": "Esporta anche in PDF",
        "card.session_summary": "Riepilogo sessione",
        "button.next_mapping": "Avanti: Mappatura",
        "summary.workbook": "File Excel: {value}",
        "summary.template": "Modello: {value}",
        "summary.output_folder": "Cartella output: {value}",
        "summary.certificate_type": "Tipo certificato: {value}",
        "summary.mappings_configured": "Mappature configurate: {count}",
        "page.mapping.title": "Mappatura",
        "page.mapping.description": "Crea mappature esplicite tra i segnaposto letterali usati nel modello e le colonne disponibili nel file Excel.",
        "group.workbook_columns": "Colonne file Excel",
        "status.no_workbook_loaded": "Nessun file Excel caricato.",
        "status.select_workbook_for_columns": "Seleziona un file Excel nella pagina Configurazione per vedere le colonne disponibili.",
        "status.could_not_inspect_workbook": "Impossibile leggere il file Excel: {error}",
        "status.rows_detected": "{row_count} righe rilevate in {path}",
        "hint.columns_panel": "Fai doppio clic su una colonna per creare rapidamente una riga di mappatura, oppure selezionala e usa il pulsante qui sotto.",
        "group.placeholder_mappings": "Mappature segnaposto",
        "hint.mapping_editor": "Usa il testo esatto del segnaposto presente nel modello Word, per esempio <<NOME>>.",
        "status.select_template_for_placeholders": "Seleziona un modello Word per rilevare segnaposto come <<NOME>>.",
        "status.detected_template_placeholders": "Rilevati {count} segnaposto",
        "status.no_template_placeholders_detected": "Nel modello selezionato non sono stati rilevati segnaposto <...>.",
        "status.could_not_inspect_template": "Impossibile analizzare i segnaposto del modello: {error}",
        "table.placeholder": "Segnaposto",
        "table.excel_column": "Colonna Excel",
        "button.add_mapping": "Aggiungi mappatura",
        "button.remove_selected": "Rimuovi selezionata",
        "button.refresh_mapping_data": "Aggiorna",
        "button.use_selected_column": "Usa colonna selezionata",
        "label.validation": "Validazione",
        "status.ready_to_generate": "Pronto per generare i certificati.",
        "status.validation_issues": "{count} elementi da correggere prima di continuare.",
        "status.validation_ready_detail": "Va tutto bene. Puoi continuare con la generazione.",
        "button.back": "Indietro",
        "button.next_generate": "Avanti: Generazione",
        "page.generate.title": "Generazione",
        "page.generate.description": "Controlla il batch corrente, valida gli input e avvia la generazione dei documenti.",
        "group.batch_summary": "Riepilogo batch",
        "group.generation_log": "Log generazione",
        "button.generate_certificates": "Genera certificati",
        "summary.output": "Output: {value}",
        "summary.mappings": "Mappature: {count}",
        "summary.export_pdf_enabled": "Esporta PDF: {value}",
        "summary.validation": "Validazione",
        "summary.ready_to_generate_short": "- Pronto per generare",
        "log.generation_finished": "Generazione completata.",
        "log.generation_failed": "Generazione non riuscita: {error}",
        "page.results.title": "Risultati",
        "page.results.description": "Controlla l'output dell'ultima esecuzione, apri i file generati e verifica eventuali errori.",
        "status.no_generation_results": "Nessun risultato di generazione disponibile.",
        "group.generated_files": "File generati",
        "group.errors": "Errori",
        "button.open_output_folder": "Apri cartella output",
        "button.open_log": "Apri log",
        "results.created_docx": "Creati {success_count} certificati DOCX su {total_rows}.",
        "results.generated_pdfs": "PDF generati: {count}",
        "results.files_listed": "File elencati: {count}",
        "results.last_certificate_number": "Ultimo numero attestato: {value}",
        "results.log_file": "File di log: {path}",
        "results.no_generation_errors": "Nessun errore di generazione.",
        "runtime.select_excel_workbook": "Seleziona un file Excel.",
        "runtime.excel_file_not_found": "File Excel non trovato: {path}",
        "runtime.select_word_template": "Seleziona un modello Word per il certificato.",
        "runtime.template_file_not_found": "Modello non trovato: {path}",
        "runtime.choose_output_folder": "Scegli una cartella di output.",
        "runtime.output_not_writable": "La cartella di output non è scrivibile: {error}",
        "runtime.license_file_not_found": "File licenza non trovato: {path}",
        "runtime.add_placeholder_mapping": "Aggiungi almeno una mappatura segnaposto.",
        "runtime.cannot_read_excel": "Impossibile leggere il file Excel: {error}",
        "runtime.mapping_missing_placeholder": "Nella riga di mappatura {row} manca il segnaposto.",
        "runtime.placeholder_duplicate": "Il segnaposto '{placeholder}' è mappato più di una volta.",
        "runtime.mapping_missing_column": "Nella riga di mappatura {row} manca la colonna Excel.",
        "runtime.column_not_available": "La colonna Excel '{column}' non è disponibile nel file selezionato.",
        "runtime.failed_generate_row": "Generazione della riga {row} non riuscita: {error}",
        "runtime.spire_not_installed": "Spire.Doc non è installato. Installa la dipendenza runtime prima di generare i certificati.",
    },
}


class LocalizationManager(QObject):
    language_changed = Signal(str)
    supported_languages = ("en", "it")

    def __init__(self, config: dict | None = None):
        super().__init__()
        config = config or {}
        app_name = str(config.get("APP_NAME", "Document Mapper")).strip() or "Document Mapper"
        organization = str(config.get("APP_ORGANIZATION", "Document Mapper")).strip() or "Document Mapper"
        default_language = self._normalize_language(config.get("APP_LANGUAGE", "en"))

        self._settings = QSettings(organization, app_name)
        saved_language = self._normalize_language(self._settings.value("ui/language", default_language))
        self._language = saved_language or default_language

    @property
    def current_language(self) -> str:
        return self._language

    def set_language(self, language: str):
        normalized = self._normalize_language(language)
        if normalized == self._language:
            return
        self._language = normalized
        self._settings.setValue("ui/language", normalized)
        self.language_changed.emit(normalized)

    def t(self, key: str, **kwargs) -> str:
        translations = TRANSLATIONS.get(self._language, TRANSLATIONS["en"])
        value = translations.get(key, TRANSLATIONS["en"].get(key, key))
        if kwargs:
            return value.format(**kwargs)
        return value

    def translate_runtime_text(self, message: str) -> str:
        if self._language == "en" or not message:
            return message

        exact = {
            "Select an Excel workbook.": self.t("runtime.select_excel_workbook"),
            "Select a Word certificate template.": self.t("runtime.select_word_template"),
            "Choose an output folder.": self.t("runtime.choose_output_folder"),
            "Add at least one placeholder mapping.": self.t("runtime.add_placeholder_mapping"),
            "Spire.Doc is not installed. Install the runtime dependency before generating certificates.": self.t(
                "runtime.spire_not_installed"
            ),
        }
        if message in exact:
            return exact[message]

        patterns = (
            (r"^Excel file not found: (?P<path>.+)$", "runtime.excel_file_not_found", "path"),
            (r"^Template file not found: (?P<path>.+)$", "runtime.template_file_not_found", "path"),
            (r"^Output folder is not writable: (?P<error>.+)$", "runtime.output_not_writable", "error"),
            (r"^License file not found: (?P<path>.+)$", "runtime.license_file_not_found", "path"),
            (r"^Cannot read Excel workbook: (?P<error>.+)$", "runtime.cannot_read_excel", "error"),
            (r"^Mapping row (?P<row>\d+) is missing a placeholder\.$", "runtime.mapping_missing_placeholder", "row"),
            (r"^Placeholder '(?P<placeholder>.+)' is mapped more than once\.$", "runtime.placeholder_duplicate", "placeholder"),
            (r"^Mapping row (?P<row>\d+) is missing an Excel column\.$", "runtime.mapping_missing_column", "row"),
            (
                r"^Excel column '(?P<column>.+)' is not available in the selected workbook\.$",
                "runtime.column_not_available",
                "column",
            ),
            (r"^Failed to generate row (?P<row>\d+): (?P<error>.+)$", "runtime.failed_generate_row", None),
        )

        for pattern, key, primary_name in patterns:
            match = re.match(pattern, message)
            if not match:
                continue
            groups = match.groupdict()
            if primary_name is None:
                return self.t(key, **groups)
            return self.t(key, **groups)

        return message

    @staticmethod
    def _normalize_language(language: object) -> str:
        candidate = str(language or "").strip().lower()
        if candidate in TRANSLATIONS:
            return candidate
        return "en"
