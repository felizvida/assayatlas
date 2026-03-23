(() => {
  const statusClassNames = ["status-success", "status-progress", "status-warning", "status-neutral"];

  function updateStatusPill(element, statusText, toneValue) {
    element.textContent = statusText || "";
    for (const className of statusClassNames) {
      element.classList.remove(className);
    }
    element.classList.add(`status-${toneValue || "neutral"}`);
  }

  function applyRecordToScope(scope, record) {
    scope.querySelectorAll("[data-bind]").forEach((element) => {
      const field = element.dataset.bind;
      if (!(field in record)) {
        return;
      }
      element.textContent = record[field] ?? "";
    });

    scope.querySelectorAll("[data-bind-status]").forEach((element) => {
      updateStatusPill(
        element,
        record[element.dataset.bindStatus],
        record[element.dataset.bindTone || "tone"],
      );
    });
  }

  async function submitEditorForm(form) {
    const statusElement = form.querySelector("[data-editor-status]");
    const submitButton = form.querySelector('button[type="submit"]');
    const scope = document.querySelector(`[data-editor-scope="${form.dataset.editorScope}"]`) || document;
    const payload = {};

    form.querySelectorAll("[name]").forEach((field) => {
      if (field.disabled) {
        return;
      }
      payload[field.name] = field.value.trim();
    });

    if (statusElement) {
      statusElement.textContent = "Saving changes...";
      statusElement.dataset.state = "progress";
    }
    if (submitButton) {
      submitButton.disabled = true;
    }

    try {
      const response = await fetch(form.dataset.endpoint, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Unable to save changes.");
      }
      const record = data[form.dataset.recordKey];
      applyRecordToScope(scope, record);
      if (statusElement) {
        statusElement.textContent = "Saved to the workspace.";
        statusElement.dataset.state = "success";
      }
    } catch (error) {
      if (statusElement) {
        statusElement.textContent = error.message;
        statusElement.dataset.state = "error";
      }
    } finally {
      if (submitButton) {
        submitButton.disabled = false;
      }
    }
  }

  document.querySelectorAll("[data-inline-editor]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      await submitEditorForm(form);
    });

    form.addEventListener("reset", () => {
      const statusElement = form.querySelector("[data-editor-status]");
      if (statusElement) {
        statusElement.textContent = "Edits reset to the last loaded values.";
        statusElement.dataset.state = "neutral";
      }
    });
  });
})();
