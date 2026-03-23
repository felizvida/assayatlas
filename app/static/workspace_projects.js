(() => {
  function setStatus(element, text, state) {
    if (!element) {
      return;
    }
    element.textContent = text;
    element.dataset.state = state;
  }

  const form = document.querySelector("[data-project-create-form]");
  if (!form) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const statusElement = form.querySelector("[data-project-create-status]");
    const submitButton = form.querySelector('button[type="submit"]');
    const payload = {};

    form.querySelectorAll("[name]").forEach((field) => {
      payload[field.name] = field.value.trim();
    });

    setStatus(statusElement, "Creating project workspace...", "progress");
    if (submitButton) {
      submitButton.disabled = true;
    }

    try {
      const response = await fetch(form.dataset.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Unable to create project workspace.");
      }
      setStatus(statusElement, "Project created. Opening workspace...", "success");
      window.location.href = data.location || `/projects/${encodeURIComponent(data.project.slug)}`;
    } catch (error) {
      setStatus(statusElement, error.message, "error");
    } finally {
      if (submitButton) {
        submitButton.disabled = false;
      }
    }
  });

  form.addEventListener("reset", () => {
    window.requestAnimationFrame(() => {
      setStatus(
        form.querySelector("[data-project-create-status]"),
        "Form reset. Ready to create a new persisted project workspace.",
        "neutral",
      );
    });
  });
})();
