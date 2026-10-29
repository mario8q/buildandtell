(function () {
  'use strict';

  const dialog = document.getElementById('voice-call-dialog');
  if (!dialog) return;

  const tokenUrl = dialog.dataset.tokenUrl;
  const vendorSrc = dialog.dataset.vendorSrc;
  const serverMaxSeconds = Number(dialog.dataset.maxSeconds) || 120;

  const startButton = dialog.querySelector('[data-voice-start]');
  const muteButton = dialog.querySelector('[data-voice-mute]');
  const endButton = dialog.querySelector('[data-voice-end]');
  const closeButtons = dialog.querySelectorAll('[data-voice-close]');
  const statusText = dialog.querySelector('[data-voice-status]');
  const statusDot = dialog.querySelector('[data-voice-dot]');
  const timerText = dialog.querySelector('[data-voice-timer]');
  const captions = dialog.querySelector('[data-voice-captions]');
  const emptyCaptions = dialog.querySelector('[data-voice-empty]');
  const errorText = dialog.querySelector('[data-voice-error]');
  const languageInputs = dialog.querySelectorAll('input[name="voice-language"]');
  const openButtons = document.querySelectorAll('[data-voice-open]');

  let conversation = null;
  let vendorPromise = null;
  let timerId = null;
  let timeLeft = serverMaxSeconds;
  let starting = false;
  let ending = false;
  let muted = false;

  function getCookie(name) {
    const match = document.cookie.match(
      new RegExp('(^|;\\s*)' + name + '=([^;]*)')
    );
    return match ? decodeURIComponent(match[2]) : '';
  }

  function formatTime(seconds) {
    const safe = Math.max(0, Math.floor(seconds));
    const mins = Math.floor(safe / 60);
    const secs = safe % 60;
    return String(mins).padStart(2, '0') + ':' + String(secs).padStart(2, '0');
  }

  function setTimer(seconds) {
    timeLeft = Math.max(0, Math.floor(seconds));
    if (timerText) timerText.textContent = formatTime(timeLeft);
  }

  function stopTimer() {
    if (timerId !== null) {
      window.clearInterval(timerId);
      timerId = null;
    }
  }

  function startTimer(seconds) {
    stopTimer();
    setTimer(seconds);
    timerId = window.setInterval(function () {
      timeLeft -= 1;
      if (timeLeft <= 0) {
        setTimer(0);
        stopTimer();
        void endCall();
        return;
      }
      setTimer(timeLeft);
    }, 1000);
  }

  function setStatus(text, state) {
    if (statusText) statusText.textContent = text;
    if (statusDot) {
      statusDot.className = 'voice-dialog__dot';
      if (state) statusDot.classList.add('is-' + state);
    }
  }

  function showError(message) {
    if (!errorText) return;
    errorText.textContent = message;
    errorText.hidden = false;
  }

  function clearError() {
    if (!errorText) return;
    errorText.textContent = '';
    errorText.hidden = true;
  }

  function clearCaptions() {
    if (!captions) return;
    captions.textContent = '';
    const hint = document.createElement('p');
    hint.className = 'voice-dialog__captions-empty';
    hint.setAttribute('data-voice-empty', '');
    hint.textContent =
      'The live transcript appears here during the call. It is not stored.';
    captions.appendChild(hint);
  }

  function addCaption(source, message) {
    if (!captions || !message) return;
    const hint = captions.querySelector('[data-voice-empty]');
    if (hint) hint.remove();

    const paragraph = document.createElement('p');
    paragraph.className =
      'voice-dialog__caption' +
      (source === 'ai' ? ' voice-dialog__caption--ai' : '');

    const speaker = document.createElement('span');
    speaker.className = 'voice-dialog__caption-speaker';
    speaker.textContent = source === 'ai' ? 'AI' : 'You';

    paragraph.appendChild(speaker);
    paragraph.appendChild(document.createTextNode(message));
    captions.appendChild(paragraph);

    while (captions.children.length > 80) {
      captions.removeChild(captions.firstElementChild);
    }
    captions.scrollTop = captions.scrollHeight;
  }

  function setLanguageDisabled(disabled) {
    languageInputs.forEach(function (input) {
      input.disabled = disabled;
    });
  }

  function showCallingControls() {
    if (startButton) startButton.hidden = true;
    if (endButton) endButton.hidden = false;
    if (muteButton) muteButton.hidden = false;
    setLanguageDisabled(true);
  }

  function showIdleControls() {
    if (startButton) {
      startButton.hidden = false;
      startButton.textContent = 'Start call';
    }
    if (endButton) endButton.hidden = true;
    if (muteButton) {
      muteButton.hidden = true;
      muteButton.textContent = 'Mute';
    }
    setLanguageDisabled(false);
    muted = false;
  }

  function resetCallUi(statusTextValue) {
    stopTimer();
    conversation = null;
    setTimer(serverMaxSeconds);
    setStatus(statusTextValue || 'Ready to call', '');
    showIdleControls();
  }

  function endCall() {
    if (ending) return Promise.resolve();
    ending = true;
    stopTimer();
    setStatus('Ending call...', 'connecting');
    const session = conversation;
    conversation = null;
    const finish = function () {
      ending = false;
      setStatus('Call ended', '');
      showIdleControls();
    };
    if (!session) {
      finish();
      return Promise.resolve();
    }
    return session
      .endSession()
      .catch(function () {})
      .then(finish, finish);
  }

  function loadVendor() {
    if (window.ElevenLabsClient) return Promise.resolve();
    if (vendorPromise) return vendorPromise;
    vendorPromise = new Promise(function (resolve, reject) {
      const script = document.createElement('script');
      script.src = vendorSrc;
      script.async = true;
      script.onload = function () {
        if (window.ElevenLabsClient) resolve();
        else reject(new Error('The voice client did not load.'));
      };
      script.onerror = function () {
        reject(new Error('The voice client could not be loaded.'));
      };
      document.head.appendChild(script);
    }).catch(function (error) {
      vendorPromise = null;
      throw error;
    });
    return vendorPromise;
  }

  function readLanguage() {
    let value = 'en';
    languageInputs.forEach(function (input) {
      if (input.checked) value = input.value;
    });
    return value;
  }

  async function startCall() {
    if (starting || conversation) return;
    starting = true;
    clearError();
    clearCaptions();
    showCallingControls();
    setStatus('Preparing call...', 'connecting');
    setTimer(serverMaxSeconds);

    try {
      const response = await fetch(tokenUrl, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ language: readLanguage() }),
      });
      const data = await response.json().catch(function () {
        return {};
      });
      if (!response.ok) {
        throw new Error(data.error || 'The call could not be started.');
      }
      if (!data.token) {
        throw new Error('The call could not be started.');
      }

      if (data.max_seconds) setTimer(data.max_seconds);

      await loadVendor();
      const api = window.ElevenLabsClient;
      if (!api || !api.Conversation) {
        throw new Error('The voice client did not load.');
      }

      setStatus('Connecting...', 'connecting');
      await api.Conversation.startSession({
        conversationToken: data.token,
        connectionType: 'webrtc',
        onConversationCreated: function (session) {
          conversation = session;
        },
        onConnect: function () {
          setStatus('Live', 'live');
          setTimer(data.max_seconds || serverMaxSeconds);
          startTimer(data.max_seconds || serverMaxSeconds);
          if (muteButton) muteButton.hidden = false;
        },
        onStatusChange: function (event) {
          if (!event || !event.status) return;
          if (event.status === 'connecting') {
            setStatus('Connecting...', 'connecting');
          } else if (event.status === 'connected') {
            setStatus('Live', 'live');
          } else if (event.status === 'disconnecting') {
            setStatus('Ending call...', 'connecting');
          }
        },
        onModeChange: function (event) {
          if (!event || !conversation) return;
          if (event.mode === 'speaking') {
            setStatus('AI is speaking', 'speaking');
          } else {
            setStatus('Listening', 'live');
          }
        },
        onMessage: function (event) {
          if (!event) return;
          addCaption(event.source, event.message);
        },
        onDisconnect: function () {
          stopTimer();
          conversation = null;
          showIdleControls();
          if (!ending) {
            setStatus('Call ended', '');
          }
        },
        onError: function (message) {
          showError(
            typeof message === 'string' && message
              ? message
              : 'The call hit a problem. You can try again.'
          );
        },
      });
    } catch (error) {
      if (conversation) {
        try {
          await conversation.endSession();
        } catch (ignored) {
          // The session may already be closed.
        }
        conversation = null;
      }
      stopTimer();
      showError(
        error && error.message
          ? error.message
          : 'The call could not be started.'
      );
      setStatus('Ready to call', '');
      showIdleControls();
    } finally {
      starting = false;
    }
  }

  function toggleMute() {
    if (!conversation || typeof conversation.setMicMuted !== 'function') {
      return;
    }
    muted = !muted;
    conversation.setMicMuted(muted);
    if (muteButton) muteButton.textContent = muted ? 'Unmute' : 'Mute';
  }

  function openDialog() {
    if (typeof dialog.showModal !== 'function') return;
    if (!dialog.open) dialog.showModal();
    resetCallUi('Ready to call');
    clearError();
    clearCaptions();
    if (startButton) startButton.focus();
  }

  function requestClose() {
    if (conversation) {
      endCall().then(function () {
        dialog.close();
      });
    } else {
      dialog.close();
    }
  }

  openButtons.forEach(function (button) {
    button.addEventListener('click', function (event) {
      event.preventDefault();
      openDialog();
    });
  });

  if (startButton) startButton.addEventListener('click', startCall);
  if (muteButton) muteButton.addEventListener('click', toggleMute);
  if (endButton) endButton.addEventListener('click', function () {
    void endCall();
  });
  closeButtons.forEach(function (button) {
    button.addEventListener('click', requestClose);
  });

  dialog.addEventListener('cancel', function (event) {
    if (conversation) {
      event.preventDefault();
      requestClose();
    }
  });

  dialog.addEventListener('close', function () {
    if (conversation) {
      const session = conversation;
      conversation = null;
      session.endSession().catch(function () {});
    }
    stopTimer();
    clearError();
    clearCaptions();
    resetCallUi('Ready to call');
  });
})();
