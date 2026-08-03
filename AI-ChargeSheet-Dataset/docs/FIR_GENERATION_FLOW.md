# FIR Generation Flow

This document defines the architecture for generating FIR documents from a validated MasterCase without invoking Gemini or inventing facts.

## Pipeline

MasterCase
↓
FIRSchema
↓
Markdown Template
↓
DOCX Template
↓
PDF Rendering
↓
OCR / Evaluation Pipeline

## Responsibilities

### 1. MasterCase
The MasterCase is the only source of truth. It contains validated case information, persons, evidence, legal sections, and investigation details.

### 2. FIRSchema
The FIR schema is a layout-driven model that mirrors the real FIR form structure. It captures the fields needed for registration, complainant details, accused details, narrative, evidence, officer details, and signatures.

### 3. Markdown template
The markdown template provides the human-readable layout structure and uses placeholders for dynamic fields such as FIR number, location, complainant name, incident date, and narrative content.

### 4. DOCX template
The DOCX template preserves the visual structure of the reference FIR document. It is designed to support a final PDF that closely resembles the uploaded reference.

### 5. PDF rendering
A renderer converts the final document to PDF while preserving the section ordering and form layout.

### 6. OCR and evaluation
The generated PDF can later be inspected through OCR and downstream evaluation workflows, but this stage is not part of synthetic content generation.
