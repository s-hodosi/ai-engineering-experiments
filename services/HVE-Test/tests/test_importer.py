from app.services.importer import extract_job_details


def test_extract_job_details_uses_title_company_and_summary():
    html = """
    <html>
      <head>
        <title>Senior Python Engineer</title>
        <meta property="og:title" content="Senior Python Engineer" />
        <meta name="description" content="Build reliable services for a modern platform." />
      </head>
      <body>
        <h1>Senior Python Engineer</h1>
        <p>At Contoso Labs</p>
        <p>Remote · Seattle, WA</p>
      </body>
    </html>
    """

    details = extract_job_details("https://example.com/jobs/123", html)

    assert details["title"] == "Senior Python Engineer"
    assert details["company"] == "Contoso Labs"
    assert details["location"] == "Remote · Seattle, WA"
    assert "reliable services" in details["summary"]
