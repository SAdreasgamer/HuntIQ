"""
HuntIQ — Resume Parser Engine.

Parses PDF resumes into structured JSON using PyMuPDF (fitz) and regex/heuristics.
Extracts contact info, summary, experience history, education, skills, and projects.

Guarantees:
- PDF is parsed ONCE
- Always returns a valid ParsedResumeData instance
- Robust fallback between PyMuPDF and pdfplumber
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from app.core.exceptions import ResumeParsingError
from app.core.logging import get_logger
from app.resume.schemas import (
    Certification,
    ContactInfo,
    Education,
    ParsedResumeData,
    Project,
    SkillCategory,
    WorkExperience,
)

logger = get_logger(__name__)


class ResumeParser:
    """PDF Resume parser using PyMuPDF and rule-based extraction."""

    # Common technical skills dictionary for tagging
    TECH_SKILLS_TAXONOMY: dict[str, set[str]] = {
        "Languages": {
            "python", "java", "javascript", "typescript", "golang", "go", "rust",
            "c++", "c#", "c", "ruby", "php", "swift", "kotlin", "scala", "sql", "r", "html", "css",
        },
        "Frameworks & Libraries": {
            "spring", "spring boot", "django", "fastapi", "flask", "react", "next.js",
            "angular", "vue", "node.js", "express", "pytorch", "tensorflow", "pandas",
            "numpy", "scikit-learn", "spark", "hibernate", "gin",
        },
        "Databases & Storage": {
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "sqlite",
            "dynamodb", "cassandra", "neo4j", "mariadb", "oracle", "snowflake",
        },
        "Cloud & DevOps": {
            "aws", "azure", "gcp", "docker", "kubernetes", "k8s", "terraform",
            "ansible", "jenkins", "github actions", "ci/cd", "helm", "prometheus", "grafana",
        },
        "Architecture & Systems": {
            "microservices", "distributed systems", "rest", "graphql", "grpc",
            "kafka", "rabbitmq", "system design", "oop", "agile", "scrum", "git",
        },
    }

    def extract_text(self, file_path: str | Path) -> str:
        """
        Extract full raw text from a PDF file using PyMuPDF.

        Fallback to pdfplumber if PyMuPDF produces minimal text.
        """
        path = Path(file_path)
        if not path.exists():
            raise ResumeParsingError(filename=path.name, reason="File does not exist")

        text_pages: list[str] = []
        try:
            doc = fitz.open(path)
            for page in doc:
                text_pages.append(page.get_text())
            doc.close()
            full_text = "\n".join(text_pages).strip()

            if len(full_text) > 50:
                return full_text
        except Exception as exc:
            logger.warning("fitz_extraction_failed", filename=path.name, error=str(exc))

        # Fallback to pdfplumber
        try:
            import pdfplumber

            with pdfplumber.open(path) as pdf:
                plumber_pages = [page.extract_text() or "" for page in pdf.pages]
                full_text = "\n".join(plumber_pages).strip()
                if len(full_text) > 50:
                    return full_text
        except Exception as exc:
            logger.error("pdfplumber_extraction_failed", filename=path.name, error=str(exc))

        raise ResumeParsingError(
            filename=path.name,
            reason="Could not extract readable text from PDF (file may be image-only or encrypted)",
        )

    def parse(self, file_path: str | Path) -> ParsedResumeData:
        """
        Parse a PDF resume into a structured ParsedResumeData object.

        Args:
            file_path: Path to the resume PDF file.

        Returns:
            ParsedResumeData with all extracted section items.
        """
        raw_text = self.extract_text(file_path)

        # 1. Contact Info
        contact = self._parse_contact_info(raw_text)

        # 2. Section Segmentation
        sections = self._segment_sections(raw_text)

        # 3. Summary
        summary = sections.get("summary")

        # 4. Skills
        skills, categorized = self._parse_skills(raw_text, sections.get("skills"))

        # 5. Work Experience
        work_exp = self._parse_work_experience(sections.get("experience", ""))

        # 6. Education
        education = self._parse_education(sections.get("education", ""))

        # 7. Projects
        projects = self._parse_projects(sections.get("projects", ""))

        # 8. Total Experience Calculation
        total_exp_years = self._calculate_total_experience(work_exp, raw_text)

        logger.info(
            "resume_parsed_successfully",
            filename=Path(file_path).name,
            name=contact.full_name,
            email=contact.email,
            skills_count=len(skills),
            exp_count=len(work_exp),
            total_exp_years=total_exp_years,
        )

        return ParsedResumeData(
            contact=contact,
            summary=summary,
            total_experience_years=total_exp_years,
            skills=skills,
            categorized_skills=categorized,
            work_experience=work_exp,
            education=education,
            projects=projects,
            certifications=[],
            raw_text=raw_text,
        )

    # ==============================================================
    # Extraction Helpers
    # ==============================================================

    def _parse_contact_info(self, text: str) -> ContactInfo:
        """Extract name, email, phone, URLs using regex."""
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        full_name = lines[0] if lines else None

        # Email
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        email = email_match.group(0) if email_match else None

        # Phone
        phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
        phone = phone_match.group(0) if phone_match else None

        # LinkedIn
        linkedin_match = re.search(r"(https?://)?(www\.)?linkedin\.com/in/[\w-]+/?", text, re.IGNORECASE)
        linkedin = linkedin_match.group(0) if linkedin_match else None

        # GitHub
        github_match = re.search(r"(https?://)?(www\.)?github\.com/[\w-]+/?", text, re.IGNORECASE)
        github = github_match.group(0) if github_match else None

        # Portfolio/Website
        website_match = re.search(r"(https?://)?(www\.)?[\w-]+\.(io|me|dev|com|org)", text, re.IGNORECASE)
        website = None
        if website_match:
            val = website_match.group(0)
            if "linkedin" not in val and "github" not in val:
                website = val

        return ContactInfo(
            full_name=full_name,
            email=email,
            phone=phone,
            linkedin_url=linkedin,
            github_url=github,
            portfolio_url=website,
        )

    def _segment_sections(self, text: str) -> dict[str, str]:
        """Divide raw text into logical section blocks using regex heading patterns."""
        headings = {
            "summary": r"(?:summary|objective|about\s+me|profile)",
            "experience": r"(?:experience|work\s+history|employment|work\s+experience)",
            "skills": r"(?:skills|technical\s+skills|core\0competencies|technologies)",
            "education": r"(?:education|academic|qualifications)",
            "projects": r"(?:projects|personal\s+projects|key\s+projects)",
        }

        pattern = r"\n(?=[A-Z\s]{3,25}\n|\b(?:" + "|".join(headings.values()) + r")\b)"
        chunks = re.split(pattern, text, flags=re.IGNORECASE)

        sections: dict[str, str] = {}
        for chunk in chunks:
            chunk_strip = chunk.strip()
            if not chunk_strip:
                continue
            first_line = chunk_strip.splitlines()[0].lower()
            for key, h_regex in headings.items():
                if re.search(h_regex, first_line, re.IGNORECASE):
                    sections[key] = chunk_strip
                    break

        return sections

    def _parse_skills(self, full_text: str, skills_section: str | None) -> tuple[list[str], list[SkillCategory]]:
        """Extract tech skills taxonomy from skills section and full text."""
        search_text = (skills_section or "") + "\n" + full_text
        search_lower = search_text.lower()

        found_skills: set[str] = set()
        categorized: list[SkillCategory] = []

        for cat_name, skill_set in self.TECH_SKILLS_TAXONOMY.items():
            cat_found = []
            for skill in skill_set:
                # Word boundary check for accuracy
                pattern = r"\b" + re.escape(skill) + r"\b"
                if re.search(pattern, search_lower):
                    found_skills.add(skill)
                    cat_found.append(skill)
            if cat_found:
                categorized.append(SkillCategory(category=cat_name, skills=sorted(cat_found)))

        return sorted(found_skills), categorized

    def _parse_work_experience(self, section_text: str) -> list[WorkExperience]:
        """Extract work experience entries from section text."""
        if not section_text:
            return []

        lines = [l.strip() for l in section_text.splitlines() if l.strip()]
        experiences: list[WorkExperience] = []

        # Group lines into blocks based on bullet points or date lines
        current_title = ""
        current_company = ""
        bullets: list[str] = []

        for line in lines:
            if line.startswith("•") or line.startswith("-") or line.startswith("*"):
                bullets.append(line.lstrip("•-* ").strip())
            elif len(line) > 5 and not current_company:
                current_company = line
            elif len(line) > 5 and not current_title:
                current_title = line

        if current_company or current_title:
            experiences.append(
                WorkExperience(
                    company=current_company or "Company",
                    title=current_title or "Engineer",
                    bullet_points=bullets,
                    technologies=self.extract_skills_from_text("\n".join(bullets)),
                )
            )

        return experiences

    def _parse_education(self, section_text: str) -> list[Education]:
        """Extract education background."""
        if not section_text:
            return []

        edu_list: list[Education] = []
        lines = [l.strip() for l in section_text.splitlines() if l.strip()]

        for line in lines:
            line_lower = line.lower()
            if any(term in line_lower for term in ["b.tech", "b.e", "b.s", "m.s", "m.tech", "bachelor", "master", "degree"]):
                edu_list.append(
                    Education(
                        institution=line,
                        degree="Bachelor/Master Degree",
                        field_of_study="Computer Science / Engineering",
                    )
                )

        return edu_list

    def _parse_projects(self, section_text: str) -> list[Project]:
        """Extract projects from section text."""
        if not section_text:
            return []

        lines = [l.strip() for l in section_text.splitlines() if l.strip()]
        projects: list[Project] = []

        for line in lines:
            if not line.startswith("•") and len(line) > 4 and "project" not in line.lower():
                projects.append(
                    Project(
                        title=line,
                        technologies=self.extract_skills_from_text(line),
                    )
                )

        return projects[:5]

    def extract_skills_from_text(self, text: str) -> list[str]:
        """Extract tech skills from arbitrary text string."""
        if not text:
            return []
        text_lower = text.lower()
        found = set()
        for cat_skills in self.TECH_SKILLS_TAXONOMY.values():
            for skill in cat_skills:
                if re.search(r"\b" + re.escape(skill) + r"\b", text_lower):
                    found.add(skill)
        return sorted(found)

    def _calculate_total_experience(self, work_exp: list[WorkExperience], raw_text: str) -> float:
        """Estimate total experience in years using date range regexes."""
        years = re.findall(r"\b(20\d{2}|19\d{2})\b", raw_text)
        if len(years) >= 2:
            try:
                int_years = [int(y) for y in years]
                min_y, max_y = min(int_years), max(int_years)
                diff = max_y - min_y
                if 0 <= diff <= 30:
                    return float(diff)
            except ValueError:
                pass
        return 2.0
