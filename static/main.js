document.addEventListener("DOMContentLoaded", () => {
  const generateBtn = document.getElementById("generate-plan-btn");
  const extraInfoInput = document.getElementById("extra-info");
  const planOutput = document.getElementById("plan-output");
  const loading = document.getElementById("loading");

  generateBtn.addEventListener("click", async () => {
    planOutput.textContent = "";
    loading.style.display = "block";

    try {
      const res = await fetch("/api/plan", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          extra_info: extraInfoInput.value,
        }),
      });

      const data = await res.json();

      if (!res.ok || data.error) {
        planOutput.textContent = "Error: " + (data.error || "Unknown error");
      } else {
        planOutput.textContent = data.plan;
      }
    } catch (err) {
      planOutput.textContent = "Request failed: " + err.message;
    } finally {
      loading.style.display = "none";
    }
  });
});