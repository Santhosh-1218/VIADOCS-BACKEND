backend/
│
├── app.py
│
├── config/
│   ├── __init__.py
│   ├── mongo.py
│   └── fonts/
│
├── routes/
│   ├── __init__.py
│   │
│   ├── auth_routes.py
│   ├── contact_routes.py
│   ├── docai_routes.py
│   ├── docs_routes.py
│   ├── feedback_routes.py
│   ├── profile_routes.py
│   ├── tools_routes.py
│   ├── user_routes.py
│   │
│   └── tools/
│       ├── __init__.py
│       ├── doc_translator_routes.py
│       ├── esign_pdf_routes.py
│       ├── excel_to_pdf_routes.py
│       ├── image_to_pdf_routes.py
│       ├── password_protect_routes.py
│       ├── pdf_compress_routes.py
│       ├── pdf_editor_routes.py
│       ├── pdf_merge_routes.py
│       ├── pdf_split_routes.py
│       ├── pdf_to_image_routes.py
│       ├── pdf_to_word_routes.py
│       ├── powerpoint_to_pdf_routes.py
│       ├── unlock_pdf_routes.py
│       └── word_to_pdf_routes.py
│
├── utils/
│   └── (optional utility scripts like file handlers, pdf helpers, etc.)
│
├── uploads/
│   ├── doc_images/
│   ├── excel-to-pdf/
│   ├── image-to-pdf/
│   ├── password-protect/
│   ├── pdf-compress/
│   ├── pdf-merge/
│   ├── pdf-split/
│   ├── pdf-to-image/
│   ├── pdf-to-word/
│   ├── powerpoint-to-pdf/
│   ├── profile_images/
│   ├── unlock-pdf/
│   └── word-to-pdf/
│
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── venv312/
