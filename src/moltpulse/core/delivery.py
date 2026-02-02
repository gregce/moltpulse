"""Delivery mechanisms for MoltPulse reports."""

import json
import os
import smtplib
from abc import ABC, abstractmethod
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, Optional

from .lib import schema
from .profile_loader import ProfileConfig


class DeliveryResult:
    """Result from a delivery attempt."""

    def __init__(
        self,
        success: bool,
        channel: str,
        message: str = "",
        error: Optional[str] = None,
    ):
        self.success = success
        self.channel = channel
        self.message = message
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "channel": self.channel,
            "message": self.message,
            "error": self.error,
        }


class Deliverer(ABC):
    """Abstract base class for delivery mechanisms."""

    @property
    @abstractmethod
    def channel(self) -> str:
        """Return the channel identifier."""
        pass

    @abstractmethod
    def deliver(
        self,
        report: schema.Report,
        config: Dict[str, Any],
        format: str = "markdown",
    ) -> DeliveryResult:
        """Deliver a report.

        Args:
            report: The report to deliver
            config: Channel-specific configuration
            format: Output format ('markdown', 'html', 'json')

        Returns:
            DeliveryResult
        """
        pass


class FileDeliverer(Deliverer):
    """Deliver reports to local files."""

    @property
    def channel(self) -> str:
        return "file"

    def deliver(
        self,
        report: schema.Report,
        config: Dict[str, Any],
        format: str = "markdown",
    ) -> DeliveryResult:
        try:
            # Get output directory
            output_dir = Path(config.get("path", "~/moltpulse-reports")).expanduser()
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report.domain}_{report.report_type}_{timestamp}"

            if format == "json":
                filepath = output_dir / f"{filename}.json"
                with open(filepath, "w") as f:
                    json.dump(report.to_dict(), f, indent=2)
            elif format == "html":
                filepath = output_dir / f"{filename}.html"
                html_content = format_report_html(report)
                with open(filepath, "w") as f:
                    f.write(html_content)
            else:  # markdown
                filepath = output_dir / f"{filename}.md"
                md_content = format_report_markdown(report)
                with open(filepath, "w") as f:
                    f.write(md_content)

            return DeliveryResult(
                success=True,
                channel="file",
                message=f"Report saved to {filepath}",
            )
        except Exception as e:
            return DeliveryResult(
                success=False,
                channel="file",
                error=str(e),
            )


class EmailDeliverer(Deliverer):
    """Deliver reports via email."""

    @property
    def channel(self) -> str:
        return "email"

    def deliver(
        self,
        report: schema.Report,
        config: Dict[str, Any],
        format: str = "html",
    ) -> DeliveryResult:
        try:
            to_addr = config.get("to")
            if not to_addr:
                return DeliveryResult(
                    success=False,
                    channel="email",
                    error="No 'to' address specified",
                )

            subject_prefix = config.get("subject_prefix", "[MoltPulse]")
            subject = f"{subject_prefix} {report.title}"

            # Get SMTP config from environment
            smtp_host = os.environ.get("SMTP_HOST", "localhost")
            smtp_port = int(os.environ.get("SMTP_PORT", "587"))
            smtp_user = os.environ.get("SMTP_USER", "")
            smtp_pass = os.environ.get("SMTP_PASSWORD", "")
            from_addr = os.environ.get("SMTP_FROM", smtp_user or "moltpulse@localhost")

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_addr
            msg["To"] = to_addr

            # Plain text fallback
            text_content = format_report_text(report)
            msg.attach(MIMEText(text_content, "plain"))

            # HTML version
            if format == "html":
                html_content = format_report_html(report)
                msg.attach(MIMEText(html_content, "html"))

            # Send
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if smtp_user and smtp_pass:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                server.sendmail(from_addr, [to_addr], msg.as_string())

            return DeliveryResult(
                success=True,
                channel="email",
                message=f"Email sent to {to_addr}",
            )
        except Exception as e:
            return DeliveryResult(
                success=False,
                channel="email",
                error=str(e),
            )


class ConsoleDeliverer(Deliverer):
    """Deliver reports to console output."""

    @property
    def channel(self) -> str:
        return "console"

    def deliver(
        self,
        report: schema.Report,
        config: Dict[str, Any],
        format: str = "markdown",
    ) -> DeliveryResult:
        try:
            if format == "json":
                content = json.dumps(report.to_dict(), indent=2)
            elif format == "compact":
                content = format_report_compact(report)
            else:
                content = format_report_markdown(report)

            print(content)

            return DeliveryResult(
                success=True,
                channel="console",
                message="Report printed to console",
            )
        except Exception as e:
            return DeliveryResult(
                success=False,
                channel="console",
                error=str(e),
            )


# Formatting functions

def format_report_markdown(report: schema.Report) -> str:
    """Format report as Markdown."""
    lines = [
        f"# {report.title}",
        "",
        f"**Generated:** {report.generated_at}",
        f"**Date Range:** {report.date_range_from} to {report.date_range_to}",
        "",
    ]

    for section in report.sections:
        lines.append(f"## {section.title}")
        lines.append("")

        for item in section.items:
            # Format based on item type
            title = item.get("title") or item.get("text", "")[:80]
            url = item.get("url") or item.get("source_url", "")
            source = item.get("source_name", "")

            if url:
                lines.append(f"- [{title}]({url})")
                if source:
                    lines.append(f"  *[{source}]*")
            else:
                lines.append(f"- {title}")

            lines.append("")

    # Sources section
    if report.all_sources:
        lines.append("---")
        lines.append("")
        lines.append("## Sources")
        lines.append("")
        for i, source in enumerate(report.all_sources, 1):
            lines.append(f"{i}. [{source.name}]({source.url})")

    return "\n".join(lines)


def format_report_html(report: schema.Report) -> str:
    """Format report as HTML email."""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .meta {{ color: #666; font-size: 0.9em; margin-bottom: 20px; }}
        .item {{ margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 4px; }}
        .item a {{ color: #007bff; text-decoration: none; }}
        .source {{ color: #666; font-size: 0.85em; }}
        .sources {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; }}
        .sources ol {{ padding-left: 20px; }}
    </style>
</head>
<body>
    <h1>{report.title}</h1>
    <div class="meta">
        <strong>Generated:</strong> {report.generated_at}<br>
        <strong>Date Range:</strong> {report.date_range_from} to {report.date_range_to}
    </div>
"""

    for section in report.sections:
        html += f"    <h2>{section.title}</h2>\n"
        for item in section.items:
            title = item.get("title") or item.get("text", "")[:80]
            url = item.get("url") or item.get("source_url", "")
            source = item.get("source_name", "")

            html += '    <div class="item">\n'
            if url:
                html += f'        <a href="{url}">{title}</a>\n'
            else:
                html += f"        {title}\n"
            if source:
                html += f'        <span class="source">[{source}]</span>\n'
            html += "    </div>\n"

    if report.all_sources:
        html += '    <div class="sources">\n'
        html += "        <h2>Sources</h2>\n"
        html += "        <ol>\n"
        for source in report.all_sources:
            html += f'            <li><a href="{source.url}">{source.name}</a></li>\n'
        html += "        </ol>\n"
        html += "    </div>\n"

    html += "</body>\n</html>"
    return html


def format_report_text(report: schema.Report) -> str:
    """Format report as plain text."""
    lines = [
        report.title.upper(),
        "=" * len(report.title),
        "",
        f"Generated: {report.generated_at}",
        f"Date Range: {report.date_range_from} to {report.date_range_to}",
        "",
    ]

    for section in report.sections:
        lines.append(section.title.upper())
        lines.append("-" * len(section.title))
        lines.append("")

        for item in section.items:
            title = item.get("title") or item.get("text", "")[:80]
            url = item.get("url") or item.get("source_url", "")
            source = item.get("source_name", "")

            lines.append(f"* {title}")
            if url:
                lines.append(f"  {url}")
            lines.append("")

    if report.all_sources:
        lines.append("")
        lines.append("SOURCES")
        lines.append("-------")
        for i, source in enumerate(report.all_sources, 1):
            lines.append(f"{i}. {source.name}: {source.url}")

    return "\n".join(lines)


def format_report_compact(report: schema.Report) -> str:
    """Format report in compact form for terminal."""
    lines = [
        f"MOLTPULSE {report.report_type.upper().replace('_', ' ')} - {report.generated_at[:10]}",
        "",
    ]

    for section in report.sections:
        lines.append(f"{section.title.upper()}:")
        for item in section.items[:5]:  # Limit to 5 items per section
            title = item.get("title") or item.get("text", "")[:60]
            score = item.get("score", 0)
            lines.append(f"  [{score:2d}] {title}")
        if len(section.items) > 5:
            lines.append(f"  ... and {len(section.items) - 5} more")
        lines.append("")

    return "\n".join(lines)


# Delivery dispatcher

DELIVERERS = {
    "file": FileDeliverer,
    "email": EmailDeliverer,
    "console": ConsoleDeliverer,
}


def deliver_report(
    report: schema.Report,
    profile: ProfileConfig,
    format: str = "markdown",
) -> DeliveryResult:
    """Deliver a report using profile's delivery configuration.

    Args:
        report: Report to deliver
        profile: Profile with delivery settings
        format: Output format

    Returns:
        DeliveryResult
    """
    channel = profile.get_delivery_channel()
    config = profile.get_delivery_config()

    deliverer_class = DELIVERERS.get(channel)
    if not deliverer_class:
        return DeliveryResult(
            success=False,
            channel=channel,
            error=f"Unknown delivery channel: {channel}",
        )

    deliverer = deliverer_class()
    result = deliverer.deliver(report, config, format)

    # Try fallback if primary fails
    if not result.success:
        fallback = profile.get_fallback_delivery()
        if fallback:
            fallback_channel = fallback.get("channel")
            fallback_class = DELIVERERS.get(fallback_channel)
            if fallback_class:
                fb_deliverer = fallback_class()
                return fb_deliverer.deliver(report, fallback, format)

    return result
