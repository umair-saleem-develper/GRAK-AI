import io
try:
    from docx import Document
except Exception:
    Document = None
import PyPDF2

class DocumentParser:
    @staticmethod
    def parse_txt(content: bytes) -> str:
        return content.decode("utf-8", errors="replace")

    @staticmethod
    def parse_pdf(content: bytes) -> str:
        text = ""
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            text = f"[Error parsing PDF: {e}]"
        return text

    @staticmethod
    def parse_docx(content: bytes) -> str:
        text = ""
        try:
            doc = Document(io.BytesIO(content))
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            text = f"[Error parsing DOCX: {e}]"
        return text

    @classmethod
    def parse_image(cls, content: bytes, content_type: str, filename: str) -> str:
        info = ""
        opt_content = content
        mime = content_type if content_type and "image/" in content_type else "image/png"
        
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(content))
            width, height = img.size
            img_format = img.format or "IMAGE"
            info = f"[Attached Image: {filename} ({width}x{height}, {img_format})]"
            
            # Optimize image for rapid OCR transmission and lower latency
            if max(width, height) > 1400:
                img_copy = img.copy()
                if img_copy.mode in ('RGBA', 'LA', 'P'):
                    img_copy = img_copy.convert('RGB')
                img_copy.thumbnail((1400, 1400), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img_copy.save(buf, format="JPEG", quality=85)
                opt_content = buf.getvalue()
                mime = "image/jpeg"
        except Exception:
            info = f"[Attached Image: {filename}]"

        # Attempt OCR and transcription using Gemini Vision with safe logging and resilient timeout
        import os
        import logging
        logger = logging.getLogger(__name__)

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("[DocumentParser] Gemini Vision extraction aborted: GEMINI_API_KEY is not set.")
            return None

        def _do_ocr():
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=api_key)
                prompt = (
                    "Transcribe and extract all visible text, numbers, tables, code, labels, and details "
                    "from this image clearly, accurately, and completely."
                )
                vision_models = [
                    "gemini-3.1-flash-lite-preview",
                    "gemini-3.1-flash-lite",
                    "gemini-3.5-flash",
                    "gemini-flash-lite-latest",
                    "gemini-3-flash-preview",
                ]
                for vision_model in vision_models:
                    try:
                        logger.info(f"[DocumentParser] Attempting Gemini Vision extraction with model '{vision_model}'")
                        res = client.models.generate_content(
                            model=vision_model,
                            contents=[
                                types.Part.from_bytes(data=opt_content, mime_type=mime),
                                prompt
                            ]
                        )
                        text_length = len(res.text) if (res and res.text) else 0
                        logger.info(
                            f"[DocumentParser] Gemini Vision extraction succeeded: model='{vision_model}', "
                            f"status_code=200, text_length={text_length}"
                        )
                        if res.text and res.text.strip():
                            return res.text.strip()
                    except Exception as model_err:
                        err_type = type(model_err).__name__
                        err_code = getattr(model_err, "code", getattr(model_err, "status_code", "UNKNOWN"))
                        # Safe logging: model name, error type, status code; no secrets
                        logger.warning(
                            f"[DocumentParser] Gemini Vision extraction failed for model='{vision_model}': "
                            f"error_type={err_type}, status_code={err_code}, error_summary={str(model_err)[:100]}"
                        )
                        continue
            except Exception as client_err:
                err_type = type(client_err).__name__
                err_code = getattr(client_err, "code", getattr(client_err, "status_code", "UNKNOWN"))
                logger.error(
                    f"[DocumentParser] Gemini Vision client error: error_type={err_type}, status_code={err_code}"
                )
            return None

        import concurrent.futures
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_do_ocr)
                ocr_result = future.result(timeout=25.0)
                if ocr_result:
                    return f"{info}\nImage Content / OCR Transcription:\n{ocr_result}"
        except concurrent.futures.TimeoutError:
            logger.error("[DocumentParser] Gemini Vision extraction timed out after 25s (error_type=TimeoutError)")
        except Exception as exec_err:
            logger.error(f"[DocumentParser] Gemini Vision execution exception: error_type={type(exec_err).__name__}, detail={exec_err}")

        # If extraction failed, return None so routers/uploads.py and UI can handle it cleanly
        return None

    @classmethod
    def parse_file(cls, content: bytes, content_type: str, filename: str) -> str:
        fn_lower = filename.lower()
        ct_lower = content_type.lower() if content_type else ""

        if "pdf" in ct_lower or fn_lower.endswith(".pdf"):
            return cls.parse_pdf(content)
        elif "word" in ct_lower or "docx" in ct_lower or fn_lower.endswith(".docx"):
            return cls.parse_docx(content)
        elif "text" in ct_lower or any(fn_lower.endswith(ext) for ext in [".txt", ".md", ".csv", ".json", ".py", ".js", ".html", ".css", ".xml"]):
            return cls.parse_txt(content)
        elif "image" in ct_lower or any(fn_lower.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"]):
            return cls.parse_image(content, content_type, filename)
        else:
            # Fallback to pure text decoding for unknown formats if they are text
            try:
                return content.decode("utf-8")
            except:
                return "[Unsupported file format or binary data]"
