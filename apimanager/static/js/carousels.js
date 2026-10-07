(() => {
  'use strict';

  const $ = window.jQuery;
  const hasSlick = Boolean($ && $.fn.slick);
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const carousels = new Set();
  let layoutFrame = null;

  function layoutOptions(element) {
    const width = element.clientWidth;
    const options = {touchThreshold: Math.max(5, Math.ceil(width / 48))};
    if (['cards', 'seasons'].includes(element.dataset.carousel)) {
      const minimumWidth = parseFloat(getComputedStyle(element).getPropertyValue('--carousel-min-slide-width')) || 300;
      options.slidesToShow = Math.max(1, Math.floor(width / minimumWidth));
    }
    return options;
  }

  function updateLayout(element) {
    if (!hasSlick || !$(element).hasClass('slick-initialized') || !element.clientWidth) return;
    const slick = $(element).slick('getSlick');
    // Avoid rebuilding the track while a mouse/touch gesture is in progress.
    if (slick.dragging || slick.animating) return;
    const options = layoutOptions(element);
    if (options.slidesToShow && options.slidesToShow !== slick.options.slidesToShow) {
      $(element).slick('slickSetOption', options, true);
    } else {
      $(element).slick('slickSetOption', 'touchThreshold', options.touchThreshold, false);
      $(element).slick('setPosition');
    }
  }

  function scheduleLayout() {
    if (layoutFrame !== null) return;
    layoutFrame = requestAnimationFrame(() => {
      layoutFrame = null;
      carousels.forEach(updateLayout);
    });
  }

  const resizeObserver = typeof ResizeObserver === 'function' ? new ResizeObserver(scheduleLayout) : null;

  function allowWrappedSwipe(slick) {
    const checkNavigable = slick.checkNavigable;
    slick.checkNavigable = function(index) {
      const cloneCount = this.options.slidesToShow + (this.options.centerMode ? 1 : 0);
      // Slick's navigable range starts at -slidesToScroll (here -1).
      // Longer backward swipes can legitimately land on earlier leading clones.
      if (this.options.infinite && this.options.swipeToSlide && !this.options.fade &&
          this.slideCount > this.options.slidesToShow && index < 0 && index >= -cloneCount) {
        return index;
      }
      return checkNavigable.call(this, index);
    };
  }

  function initializeCarousel(element) {
    if (!hasSlick || !element.children.length || $(element).hasClass('slick-initialized')) return;
    const type = element.dataset.carousel;
    const options = {
      infinite: true,
      slidesToShow: 1,
      slidesToScroll: 1,
      arrows: true,
      dots: false,
      speed: reducedMotion ? 0 : 300,
      accessibility: true,
      draggable: true,
      swipe: true,
      touchMove: true,
      swipeToSlide: true,
      adaptiveHeight: ['episodes', 'images'].includes(type),
      prevArrow: '<button type="button" class="slick-prev" aria-label="Предыдущий слайд">‹</button>',
      nextArrow: '<button type="button" class="slick-next" aria-label="Следующий слайд">›</button>',
    };
    Object.assign(options, layoutOptions(element));
    if (type === 'images' || type === 'trailers') {
      options.dots = element.children.length > 1;
    }
    $(element).slick(options);
    allowWrappedSwipe($(element).slick('getSlick'));
    if (!carousels.has(element)) {
      carousels.add(element);
      if (resizeObserver) resizeObserver.observe(element);
      $(element).on('afterChange.cinemaLayout', scheduleLayout);
      // A short gesture may finish without afterChange.
      element.addEventListener('mouseup', scheduleLayout);
      element.addEventListener('touchend', scheduleLayout);
      element.addEventListener('click', event => {
        // Slick's drag suppression must not block Enter or Space afterwards.
        if (event.detail === 0 && $(element).hasClass('slick-initialized')) {
          $(element).slick('getSlick').shouldClick = true;
        }
      }, true);
    }
  }

  function destroyCarousel(element) {
    if (hasSlick && $(element).hasClass('slick-initialized')) $(element).slick('unslick');
  }

  function makeElement(tag, className, text) {
    const element = document.createElement(tag);
    element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function text(value) {
    return typeof value === 'string' ? value.trim() : '';
  }

  function episodeSlide(episode) {
    const slide = makeElement('div', 'episode-slide');
    const card = makeElement('div', 'card custom-card episode-card');
    slide.append(card);
    const number = Number.isInteger(episode.number) && episode.number > 0 ? episode.number : null;
    const poster = text(episode.poster_url);
    // API strings become text nodes, never executable HTML.
    if (poster) {
      let url;
      try { url = new URL(poster, window.location.href); } catch (error) { /* Optional invalid poster. */ }
      if (url && ['http:', 'https:'].includes(url.protocol)) {
        const image = makeElement('img', 'card-img-top episode-image');
        image.src = url.href;
        image.alt = number ? `Кадр эпизода ${number}` : 'Кадр эпизода';
        card.append(image);
      }
    }
    const body = makeElement('div', 'card-body text-center');
    card.append(body);
    if (number) body.append(makeElement('h4', 'card-title', `Эпизод ${number}`));
    body.append(makeElement('div', 'divider'));
    body.append(makeElement('h3', 'card-title', text(episode.name) || text(episode.name_en) || 'Без названия'));
    const description = text(episode.description) || text(episode.description_en);
    if (description) {
      body.append(makeElement('div', 'divider'));
      body.append(makeElement('p', 'line-clamp-4', description));
    }
    return slide;
  }

  function initializeSeasons(root) {
    if (root.dataset.seriesReady) return;
    root.dataset.seriesReady = 'true';
    const slider = root.querySelector('[data-carousel="episodes"]');
    const status = root.querySelector('[data-season-status]');
    const spinner = root.querySelector('[data-season-spinner]');
    const retry = root.querySelector('[data-season-retry]');
    const empty = root.querySelector('[data-episodes-empty]');
    // Responsive reinitialization recreates Slick's cloned season buttons.
    const buttons = () => Array.from(root.querySelectorAll('[data-season-id]'));
    let currentSeason = root.dataset.currentSeason;
    let pendingSeason = null;
    let retryTarget = null;
    let controller = null;
    let requestVersion = 0;

    function finishLoading() {
      pendingSeason = null;
      spinner.hidden = true;
      slider.setAttribute('aria-busy', 'false');
      buttons().forEach(button => {
        button.classList.remove('is-loading');
        button.removeAttribute('aria-busy');
      });
    }

    async function loadSeason(button) {
      const seasonId = button.dataset.seasonId;
      if (seasonId === pendingSeason) return;
      const version = ++requestVersion;
      if (controller) controller.abort();
      controller = null;
      finishLoading();
      retry.hidden = true;
      retryTarget = null;
      // Selecting the displayed season also cancels a pending switch.
      if (seasonId === currentSeason) {
        status.textContent = '';
        return;
      }
      pendingSeason = seasonId;
      buttons().filter(option => option.dataset.seasonId === seasonId).forEach(option => {
        option.classList.add('is-loading');
        option.setAttribute('aria-busy', 'true');
      });
      spinner.hidden = false;
      slider.setAttribute('aria-busy', 'true');
      const seasonName = button.textContent.trim();
      status.textContent = `Загружаем эпизоды: ${seasonName}…`;
      const requestController = new AbortController();
      controller = requestController;
      const timeout = window.setTimeout(() => requestController.abort(), 12000);
      try {
        const response = await fetch(button.dataset.episodesUrl, {
          signal: requestController.signal,
          credentials: 'same-origin',
          headers: {Accept: 'application/json'},
        });
        if (!response.ok) throw new Error('Episodes request failed');
        const data = await response.json();
        if (!data || !Array.isArray(data.episodes) || data.episodes.some(ep => !ep || typeof ep !== 'object' || Array.isArray(ep))) {
          throw new Error('Invalid episodes response');
        }
        const fragment = document.createDocumentFragment();
        data.episodes.forEach(episode => fragment.append(episodeSlide(episode)));
        // A slow response must never replace the more recently selected season.
        if (version !== requestVersion) return;
        destroyCarousel(slider);
        slider.replaceChildren(fragment);
        initializeCarousel(slider);
        empty.hidden = data.episodes.length > 0;
        currentSeason = seasonId;
        root.dataset.currentSeason = seasonId;
        buttons().forEach(option => {
          const selected = option.dataset.seasonId === seasonId;
          option.classList.toggle('active', selected);
          option.setAttribute('aria-pressed', String(selected));
        });
        status.textContent = `Выбран ${seasonName.toLocaleLowerCase('ru')}.`;
      } catch (error) {
        if (version !== requestVersion) return;
        status.textContent = 'Не удалось загрузить эпизоды. Попробуйте ещё раз.';
        retryTarget = button;
        retry.hidden = false;
        // Keep the previously loaded episodes and their selected season.
      } finally {
        window.clearTimeout(timeout);
        if (version === requestVersion) {
          controller = null;
          finishLoading();
        }
      }
    }

    // Slick stops dragged clicks on its list before they reach this parent.
    root.addEventListener('click', event => {
      const button = event.target.closest('[data-season-id]');
      if (button && root.contains(button)) loadSeason(button);
    });
    retry.addEventListener('click', () => {
      if (retryTarget) loadSeason(retryTarget);
    });
  }

  function start() {
    document.querySelectorAll('[data-carousel]').forEach(element => {
      initializeCarousel(element);
      // Initialize without waiting for every external image on the page.
      element.addEventListener('load', event => {
        if (event.target.tagName === 'IMG' && hasSlick && $(element).hasClass('slick-initialized')) {
          $(element).slick('setPosition');
        }
      }, true);
      if (hasSlick && element.dataset.carousel === 'trailers') {
        $(element).on('beforeChange.cinema', (event, slick, current, next) => {
          if (current === next) return;
          // Reload the hidden player so sound does not continue after switching.
          element.querySelectorAll('.slick-current iframe').forEach(frame => {
            frame.src = frame.src;
          });
        });
      }
    });
    document.querySelectorAll('[data-series-carousels]').forEach(initializeSeasons);
    window.addEventListener('resize', scheduleLayout, {passive: true});
    if (window.visualViewport) window.visualViewport.addEventListener('resize', scheduleLayout, {passive: true});
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once: true});
  else start();
})();
