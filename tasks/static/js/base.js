document.addEventListener('DOMContentLoaded',function(){
    let btn_nav = document.querySelector(".btn-menu-nav");
      const sidebar = document.querySelector(".sidebar");
      /* elemento agregado */
      const opciones = document.querySelector(".opciones_sidebar");
      /**************** */
      let m_content = document.querySelector(".main_content");
      let avatar = document.querySelector("#avatar_1");
      let panel_avatar = document.querySelector(".panel-conf");
      let icon_noti = document.querySelector("#icon_noti");
      let notificaciones = document.querySelector(".noti-panel");

      sidebarToggle();
      avatarToggle();
      notiToggle();

      function sidebarToggle() {
        btn_nav.onclick = (event) => {
          event.stopPropagation(); // Detiene la propagación del clic
          sidebar.classList.toggle("ocultar");
          opciones.classList.toggle("ocultar_f");
        };
      }

      function avatarToggle() {
        avatar.onclick = (event) => {
          event.stopPropagation();
          panel_avatar.classList.toggle("d-none");

          if (
            !notificaciones.classList.contains("d-none") &&
            !notificaciones.contains(event.target) &&
            event.target !== icon_noti
          ) {
            notificaciones.classList.add("d-none");
          }
        };
      }

      function notiToggle() {
        icon_noti.onclick = (event) => {
          event.stopPropagation(); // Detiene la propagación del clic
          notificaciones.classList.toggle("d-none");

          if (
            !panel_avatar.classList.contains("d-none") &&
            !panel_avatar.contains(event.target) &&
            event.target !== avatar
          ) {
            panel_avatar.classList.add("d-none");
          }
        };
      }

      // Evento para ocultar los elementos con clase "d-none" cuando se hace clic fuera de ellos
      document.onclick = (event) => {
        togglePanels();
      };

      function togglePanels() {
        // Si el clic no es en el avatar ni en el panel de avatar, ocultamos el panel
        if (
          !panel_avatar.classList.contains("d-none") &&
          !panel_avatar.contains(event.target) &&
          event.target !== avatar
        ) {
          panel_avatar.classList.add("d-none");
        }

        // Si el clic no es en el icono de notificación ni en el panel de notificaciones, ocultamos el panel
        if (
          !notificaciones.classList.contains("d-none") &&
          !notificaciones.contains(event.target) &&
          event.target !== icon_noti
        ) {
          notificaciones.classList.add("d-none");
        }
      }
});