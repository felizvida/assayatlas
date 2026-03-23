(() => {
  const statusToneMap = {
    Queued: "warning",
    Rendering: "progress",
    "In progress": "progress",
    "Waiting on review": "neutral",
    Blocked: "warning",
    Ready: "success",
  };

  function ensureSelectValue(field, value) {
    if (!field || !value) {
      return;
    }
    const knownOption = Array.from(field.options).find((option) => option.value === value);
    if (knownOption) {
      field.value = value;
      return;
    }
    const option = new Option(value, value, true, true);
    field.add(option, 0);
    field.value = value;
  }

  function syncToneToStatus(form) {
    const statusField = form.querySelector("[data-status-select]");
    const toneField = form.querySelector("[data-tone-select]");
    if (!statusField || !toneField) {
      return;
    }
    const suggestedTone = statusToneMap[statusField.value];
    if (suggestedTone) {
      toneField.value = suggestedTone;
    }
  }

  function setStatusMessage(element, text, state) {
    if (!element) {
      return;
    }
    element.textContent = text;
    element.dataset.state = state;
  }

  function updateStatusPill(element, statusText, toneValue) {
    if (!element) {
      return;
    }
    element.textContent = statusText || "";
    element.className = `status-pill status-${toneValue || "neutral"}`;
  }

  function applyJobToCard(card, job) {
    card.dataset.jobKey = job.job_key || "";

    const titleLink = card.querySelector("[data-export-job-link]");
    const openButton = card.querySelector("[data-export-job-open]");
    const detailElement = card.querySelector("[data-export-job-detail]");
    const statusPill = card.querySelector("[data-export-job-status]");
    const form = card.querySelector("[data-export-job-form]");

    if (titleLink) {
      titleLink.textContent = job.title || "";
      titleLink.href = job.path || "#";
    }
    if (openButton) {
      openButton.href = job.path || "#";
    }
    if (detailElement) {
      detailElement.textContent = job.detail || "";
    }
    updateStatusPill(statusPill, job.status, job.tone);

    if (form) {
      form.dataset.endpoint = `/api/export-jobs/${encodeURIComponent(job.job_key || "")}`;
      const statusField = form.querySelector('[name="status"]');
      const toneField = form.querySelector('[name="tone"]');
      const detailField = form.querySelector('[name="detail"]');
      if (statusField) {
        ensureSelectValue(statusField, job.status || "Queued");
      }
      if (toneField) {
        ensureSelectValue(toneField, job.tone || statusToneMap[job.status] || "warning");
      }
      if (detailField) {
        detailField.value = job.detail || "";
      }
    }
  }

  function buildJobCard(template, job) {
    const fragment = template.content.cloneNode(true);
    const card = fragment.querySelector("[data-export-job-card]");
    if (!card) {
      return null;
    }
    applyJobToCard(card, job);
    return card;
  }

  function registerStatusSync(form) {
    form.querySelectorAll("[data-status-select]").forEach((field) => {
      field.addEventListener("change", (event) => {
        const currentForm = event.target.closest("form");
        if (currentForm) {
          syncToneToStatus(currentForm);
        }
      });
    });
  }

  function registerJobForm(form) {
    registerStatusSync(form);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      await submitJobUpdate(form);
    });
  }

  async function submitJobUpdate(form) {
    const submitButton = form.querySelector('button[type="submit"]');
    const statusElement = form.querySelector("[data-export-job-status-message]");
    const payload = {};

    form.querySelectorAll("[name]").forEach((field) => {
      payload[field.name] = field.value.trim();
    });

    setStatusMessage(statusElement, "Saving export job...", "progress");
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
        throw new Error(data.error || "Unable to update export job.");
      }
      const card = form.closest("[data-export-job-card]");
      if (card) {
        applyJobToCard(card, data.export_job);
      }
      setStatusMessage(statusElement, "Export job saved.", "success");
    } catch (error) {
      setStatusMessage(statusElement, error.message, "error");
    } finally {
      if (submitButton) {
        submitButton.disabled = false;
      }
    }
  }

  async function submitCreateForm(form, list, template) {
    const statusElement = form.querySelector("[data-export-create-status]");
    const submitButton = form.querySelector('button[type="submit"]');
    const payload = {};

    form.querySelectorAll("[name]").forEach((field) => {
      payload[field.name] = field.value.trim();
    });

    setStatusMessage(statusElement, "Queueing export job...", "progress");
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
        throw new Error(data.error || "Unable to create export job.");
      }

      const card = buildJobCard(template, data.export_job);
      if (card) {
        list.prepend(card);
        const jobForm = card.querySelector("[data-export-job-form]");
        if (jobForm) {
          registerJobForm(jobForm);
        }
      }

      form.dataset.suppressResetMessage = "true";
      form.reset();
      syncToneToStatus(form);
      setStatusMessage(statusElement, "Export job queued in the workspace.", "success");
    } catch (error) {
      setStatusMessage(statusElement, error.message, "error");
    } finally {
      if (submitButton) {
        submitButton.disabled = false;
      }
    }
  }

  const queueRoot = document.querySelector("[data-export-queue]");
  if (!queueRoot) {
    return;
  }

  const createForm = queueRoot.querySelector("[data-export-create-form]");
  const list = queueRoot.querySelector("[data-export-job-list]");
  const template = queueRoot.querySelector("[data-export-job-template]");

  queueRoot.querySelectorAll("[data-export-job-form]").forEach((form) => {
    registerJobForm(form);
  });

  if (createForm && list && template) {
    registerStatusSync(createForm);
    syncToneToStatus(createForm);
    createForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      await submitCreateForm(createForm, list, template);
    });

    createForm.addEventListener("reset", () => {
      window.requestAnimationFrame(() => {
        if (createForm.dataset.suppressResetMessage === "true") {
          delete createForm.dataset.suppressResetMessage;
          return;
        }
        syncToneToStatus(createForm);
        setStatusMessage(
          createForm.querySelector("[data-export-create-status]"),
          "Form reset to the default queued state.",
          "neutral",
        );
      });
    });
  }
})();
