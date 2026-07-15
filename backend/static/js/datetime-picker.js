/**
 * Flatpickr dla pól daty wynajmu — spójny kalendarz zamiast natywnego datetime-local.
 */
(function () {
  function initPickers() {
    if (typeof flatpickr === "undefined") {
      return;
    }

    if (flatpickr.l10ns && flatpickr.l10ns.pl) {
      flatpickr.localize(flatpickr.l10ns.pl);
    }

    document.querySelectorAll(".js-datetime-picker").forEach(function (element) {
      if (element._flatpickr) {
        return;
      }

      flatpickr(element, {
        enableTime: true,
        time_24hr: true,
        dateFormat: "Y-m-d\\TH:i",
        altInput: true,
        altFormat: "d.m.Y, H:i",
        allowInput: true,
        minuteIncrement: 15,
        disableMobile: true,
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPickers);
  } else {
    initPickers();
  }
})();
