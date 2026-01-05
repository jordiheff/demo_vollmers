"""
FDA 2020 Nutrition Label Generator using Pillow and ReportLab.
"""

import io
import base64
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from models.nutrition import NutritionPerServing


class LabelGenerator:
    """Generate FDA 2020 compliant nutrition labels."""

    # Label dimensions (in pixels at 300 DPI)
    LABEL_WIDTH = 750  # ~2.5 inches
    LABEL_HEIGHT = 1200  # ~4 inches
    PADDING = 30
    LINE_HEIGHT = 36
    DPI = 300

    # Font sizes
    TITLE_SIZE = 48
    HEADER_SIZE = 24
    CALORIES_SIZE = 72
    NUTRIENT_SIZE = 22
    SMALL_SIZE = 18
    FOOTNOTE_SIZE = 16

    def __init__(self):
        """Initialize the label generator with fonts."""
        # Use default fonts (works cross-platform)
        # In production, you'd load specific FDA-compliant fonts
        self.fonts = {
            "title": self._get_font("bold", self.TITLE_SIZE),
            "header": self._get_font("bold", self.HEADER_SIZE),
            "calories_label": self._get_font("bold", 36),
            "calories_value": self._get_font("bold", self.CALORIES_SIZE),
            "nutrient_bold": self._get_font("bold", self.NUTRIENT_SIZE),
            "nutrient": self._get_font("regular", self.NUTRIENT_SIZE),
            "small": self._get_font("regular", self.SMALL_SIZE),
            "footnote": self._get_font("regular", self.FOOTNOTE_SIZE),
        }

    def _get_font(self, style: str, size: int) -> ImageFont.FreeTypeFont:
        """
        Get a font with fallback to default.

        Args:
            style: "bold" or "regular"
            size: Font size in pixels

        Returns:
            PIL ImageFont object
        """
        # Try common system fonts
        font_paths = {
            "bold": [
                "/System/Library/Fonts/Helvetica.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
            ],
            "regular": [
                "/System/Library/Fonts/Helvetica.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "C:/Windows/Fonts/arial.ttf",
            ]
        }

        for path in font_paths.get(style, []):
            try:
                return ImageFont.truetype(path, size)
            except (IOError, OSError):
                continue

        # Fallback to default
        return ImageFont.load_default()

    def generate(
        self,
        nutrition: NutritionPerServing,
        product_name: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate nutrition label as PNG and PDF.

        Args:
            nutrition: Per-serving nutrition values with %DV
            product_name: Optional product name for the label

        Returns:
            Tuple of (PNG base64, PDF base64)
        """
        # Generate PNG
        image = self._generate_image(nutrition)
        png_buffer = io.BytesIO()
        image.save(png_buffer, format="PNG", dpi=(self.DPI, self.DPI))
        png_base64 = base64.b64encode(png_buffer.getvalue()).decode("utf-8")

        # Generate PDF
        pdf_buffer = io.BytesIO()
        self._generate_pdf(nutrition, pdf_buffer)
        pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode("utf-8")

        return png_base64, pdf_base64

    def _generate_image(self, nutrition: NutritionPerServing) -> Image.Image:
        """
        Generate the nutrition label as a PIL Image.

        Args:
            nutrition: Per-serving nutrition values

        Returns:
            PIL Image object
        """
        # Create white background
        image = Image.new("RGB", (self.LABEL_WIDTH, self.LABEL_HEIGHT), "white")
        draw = ImageDraw.Draw(image)

        y = self.PADDING
        x_left = self.PADDING
        x_right = self.LABEL_WIDTH - self.PADDING

        # Draw border
        draw.rectangle(
            [self.PADDING - 5, self.PADDING - 5,
             self.LABEL_WIDTH - self.PADDING + 5, self.LABEL_HEIGHT - self.PADDING + 5],
            outline="black",
            width=2
        )

        # Title: "Nutrition Facts"
        draw.text((x_left, y), "Nutrition Facts", font=self.fonts["title"], fill="black")
        y += 55

        # Thick line
        draw.rectangle([x_left, y, x_right, y + 10], fill="black")
        y += 20

        # Servings info
        serving = nutrition.serving_config
        draw.text(
            (x_left, y),
            f"{int(serving.servings_per_container)} servings per container",
            font=self.fonts["nutrient"],
            fill="black"
        )
        y += self.LINE_HEIGHT

        # Serving size
        draw.text((x_left, y), "Serving size", font=self.fonts["nutrient_bold"], fill="black")
        draw.text(
            (x_right, y),
            serving.serving_size_description,
            font=self.fonts["nutrient_bold"],
            fill="black",
            anchor="ra"
        )
        y += self.LINE_HEIGHT + 10

        # Thick line
        draw.rectangle([x_left, y, x_right, y + 15], fill="black")
        y += 25

        # Amount per serving
        draw.text((x_left, y), "Amount per serving", font=self.fonts["small"], fill="black")
        y += 30

        # Calories
        draw.text((x_left, y), "Calories", font=self.fonts["calories_label"], fill="black")
        cal_str = self._format_value(nutrition.calories, "")
        draw.text((x_right, y), cal_str, font=self.fonts["calories_value"], fill="black", anchor="ra")
        y += 70

        # Thick line
        draw.rectangle([x_left, y, x_right, y + 8], fill="black")
        y += 18

        # % Daily Value header
        draw.text((x_right, y), "% Daily Value*", font=self.fonts["small"], fill="black", anchor="ra")
        y += 30

        # Thin line
        draw.line([x_left, y, x_right, y], fill="black", width=1)
        y += 8

        # Nutrient rows
        nutrients = [
            ("Total Fat", nutrition.total_fat_g, "g", nutrition.total_fat_dv, True, 0),
            ("Saturated Fat", nutrition.saturated_fat_g, "g", nutrition.saturated_fat_dv, False, 1),
            ("Trans Fat", nutrition.trans_fat_g, "g", None, False, 1),
            ("Cholesterol", nutrition.cholesterol_mg, "mg", nutrition.cholesterol_dv, True, 0),
            ("Sodium", nutrition.sodium_mg, "mg", nutrition.sodium_dv, True, 0),
            ("Total Carbohydrate", nutrition.total_carbohydrate_g, "g", nutrition.total_carbohydrate_dv, True, 0),
            ("Dietary Fiber", nutrition.dietary_fiber_g, "g", nutrition.dietary_fiber_dv, False, 1),
            ("Total Sugars", nutrition.total_sugars_g, "g", None, False, 1),
            ("Added Sugars", nutrition.added_sugars_g, "g", nutrition.added_sugars_dv, False, 2),
            ("Protein", nutrition.protein_g, "g", None, True, 0),
        ]

        for name, value, unit, dv, bold, indent in nutrients:
            y = self._draw_nutrient_row(
                draw, x_left, x_right, y,
                name, value, unit, dv, bold, indent
            )

        # Thicker line before vitamins/minerals
        draw.rectangle([x_left, y, x_right, y + 12], fill="black")
        y += 22

        # Vitamins and minerals
        vitamins = [
            ("Vitamin D", nutrition.vitamin_d_mcg, "mcg", nutrition.vitamin_d_dv),
            ("Calcium", nutrition.calcium_mg, "mg", nutrition.calcium_dv),
            ("Iron", nutrition.iron_mg, "mg", nutrition.iron_dv),
            ("Potassium", nutrition.potassium_mg, "mg", nutrition.potassium_dv),
        ]

        for name, value, unit, dv in vitamins:
            y = self._draw_vitamin_row(draw, x_left, x_right, y, name, value, unit, dv)

        # Footnote
        y += 10
        draw.line([x_left, y, x_right, y], fill="black", width=1)
        y += 10

        footnote = "* The % Daily Value tells you how much a nutrient in a serving of food contributes to a daily diet. 2,000 calories a day is used for general nutrition advice."
        self._draw_wrapped_text(draw, x_left, y, x_right - x_left, footnote, self.fonts["footnote"])

        return image

    def _draw_nutrient_row(
        self,
        draw: ImageDraw.Draw,
        x_left: int,
        x_right: int,
        y: int,
        name: str,
        value: Optional[float],
        unit: str,
        dv: Optional[int],
        bold: bool,
        indent: int
    ) -> int:
        """Draw a single nutrient row and return new y position."""
        indent_px = indent * 20
        font = self.fonts["nutrient_bold"] if bold else self.fonts["nutrient"]

        # Name and value
        value_str = self._format_value(value, unit)

        if indent == 2 and name == "Added Sugars":
            # Special formatting for added sugars
            text = f"Includes {value_str} Added Sugars"
        else:
            text = f"{name} {value_str}"

        draw.text((x_left + indent_px, y), text, font=font, fill="black")

        # %DV
        if dv is not None:
            draw.text((x_right, y), f"{dv}%", font=self.fonts["nutrient_bold"], fill="black", anchor="ra")

        y += self.LINE_HEIGHT

        # Thin line
        draw.line([x_left, y - 4, x_right, y - 4], fill="black", width=1)

        return y

    def _draw_vitamin_row(
        self,
        draw: ImageDraw.Draw,
        x_left: int,
        x_right: int,
        y: int,
        name: str,
        value: Optional[float],
        unit: str,
        dv: Optional[int]
    ) -> int:
        """Draw a vitamin/mineral row and return new y position."""
        value_str = self._format_value(value, unit)
        text = f"{name} {value_str}"

        draw.text((x_left, y), text, font=self.fonts["nutrient"], fill="black")

        if dv is not None:
            draw.text((x_right, y), f"{dv}%", font=self.fonts["nutrient"], fill="black", anchor="ra")

        y += self.LINE_HEIGHT
        draw.line([x_left, y - 4, x_right, y - 4], fill="black", width=1)

        return y

    def _format_value(self, value: Optional[float], unit: str) -> str:
        """Format a nutrition value for display."""
        if value is None:
            return f"—{unit}"

        if value == int(value):
            return f"{int(value)}{unit}"
        else:
            return f"{value:.1f}{unit}"

    def _draw_wrapped_text(
        self,
        draw: ImageDraw.Draw,
        x: int,
        y: int,
        max_width: int,
        text: str,
        font: ImageFont.FreeTypeFont
    ) -> int:
        """Draw text wrapped to max_width and return final y position."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            line_text = " ".join(current_line)
            bbox = draw.textbbox((0, 0), line_text, font=font)
            if bbox[2] > max_width:
                current_line.pop()
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        for line in lines:
            draw.text((x, y), line, font=font, fill="black")
            y += 20

        return y

    def _generate_pdf(
        self,
        nutrition: NutritionPerServing,
        buffer: io.BytesIO
    ) -> None:
        """
        Generate nutrition label as PDF.

        Args:
            nutrition: Per-serving nutrition values
            buffer: BytesIO buffer to write PDF to
        """
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Generate the image first, then embed it in PDF
        image = self._generate_image(nutrition)

        # Save image to temporary buffer
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        # Calculate position to center on page
        img_width = 2.5 * inch
        img_height = 4 * inch
        x = (width - img_width) / 2
        y = (height - img_height) / 2

        # Draw image
        from reportlab.lib.utils import ImageReader
        img_reader = ImageReader(img_buffer)
        c.drawImage(img_reader, x, y, width=img_width, height=img_height)

        c.save()
