# Custom Hardware Automation Project

Captured: 2026-10-30T10:54:00.588Z

Source: https://www.google.com/search?q=5+cent+5+euro+verhaal+dollar+jorn+leeuwerink+%28rink+ice+hockey+puck.js+NHL+97+replay+skip%29&sca_esv=cb51b3a02b3fcb3e&sxsrf=APpeQnvtNju4YlgvxdHA1wIIff7KrMNVag%3A1793083195528&udm=50&source=chrome.ob&fbs=ABfTbFVyMZGZf1hfvX9uKjN_-G8c4u0nXx4bEIpwm1lnNH832a9BVCEiB2iPJNekNderQwIgLtPdGtXl-1ukUntONsOMkLK8Wjg5QbsFQsyTdBlDyIWYhgxyDNTy0wPRmWscMhXPcoRl2IGiedJq-Ou7bktAThMu4NA9p70Yhev5koDcBW5-E_NLUvu30_BOJKw7r_p9-3Y2&vsint=&aep=1&ntc=1&cs=1&sa=X&ved=2ahUKEwji7a-3y9mXAxUE9bsIHb7wJ38Q2J8OegQIEhAD&biw=1707&bih=898&dpr=1.5&mstk=AUtExfDo0DC2PKitoxYRKFYQRi9iqDQXkYt2e6y8XK_2ZMR0XXmNsHwu16TGOu0H7cNRMixzLkSTtoZhVCDwrAxgVWIxvO4eALGjpBeIjIUiT0f7YlnPb9xF1BpdcM88IXYw8QRcrETASl7F68_xJxR7_l5IrH0GSE7hDK1-AvydMekiFdm1oGlBxePjZhzNksuGcV3FnLk02SJ7ni6y6_NWyNd3K9lM_LVUmXJ6d1DkTyY_H47-HDaTtl22BStXKKfFJMEophZFoOmm6FEdqWhUH4L96JPwNMPN917wjRfPNLVlK9kHv5TXcZ7aHZoMrrkoot0UPU7d9tDdng&csuir=1&mtid=QUfgapqVAfeM9u8P4f3UyQ4

## Prompt 1 — You

5 cent 5 euro verhaal dollar jorn leeuwerink (rink ice hockey puck.js NHL 97 replay skip)

## Response 1 — Google AI Mode

The concepts you have strung together read like a custom **macro automation or hardware hack project** utilizing a **Puck.js** (a Bluetooth-programmable smart button) to interact with retro emulators or media setups. 

![](../assets/7ee03af4254d9f856b08.png)Google

Here is how these seemingly unrelated fragments intersect into a potential project blueprint:

### 🎮 The Core Setup: NHL 97 Replay Skipper

In retro sports simulations like **NHL 97**, scoring triggers an unskippable or tedious replay sequence. 

![](../assets/0cc941a4d345b0c34b81.png)Facebook +1

* **The Puck.js Hack:** You can program a [Puck.js device](https://www.puck-js.com) via Espruino to act as a **Bluetooth HID Keyboard**.
* **The Action:** When pressed, it sends a specific keyboard macro (e.g., rapid taps of `Space`, `Esc`, or `Enter`) to automatically **skip the replay sequence** and jump straight back to the face-off rink. 

  ![](../assets/c837d6cd4f6b7873cd93.png)YouTube

### 🎬 The Narrative & Aesthetic: Jorn Leeuwerink

[Jorn Leeuwerink](https://www.aapje.net/) is a renowned Dutch animation director known for award-winning satirical short films like ***Varken* (Pig)** and ***Dog Bridge***. 

![](../assets/6b634bcf216ac612cfbc.png)Nederlands Film Festival +1

* **The Dollar / Currency Allegory:** His animations deeply explore structural societal dependencies, currency, resource consumption, and greed. 

  ![](../assets/54c84ad492bfb98c5296.png)Cartoon Brew +1
* **The "5 Cent / 5 Euro" Reference:** This appears to invoke a classic Dutch viral internet meme trope (reminiscent of the legendary *"5 euro op je muil gauw!"* confrontation) or a micro-transaction concept. In a project context, this implies a satirical **"pay-to-skip" mechanism**: physically inserting or mapping a 5-cent, 5-euro, or dollar value to bypass unskippable game features. 

  ![](../assets/0cc941a4d345b0c34b81.png)Facebook

---

### 💻 Sample Puck.js Script (HID Replay Skipper)

If you are looking to build a Bluetooth macro button that mimics a keyboard to fast-forward or skip menu/replay elements in emulated games, you can flash this script to your Puck.js:

javascript

```
var kb = require("ble_hid_keyboard");

NRF.setServices(undefined, { hid : kb.report });

// Trigger when the Puck button is pressed
setWatch(function(e) {
  var len = e.time - e.lastTime;
  
  // Quick press: Simulates hitting the skip key (e.g., Spacebar)
  if (len < 0.3) {
    kb.tap(kb.KEY.SPACE, 0, function() {
      // Optional: Add a second tap if NHL 97 requires a double-press
      setTimeout(function() {
        kb.tap(kb.KEY.SPACE, 0);
      }, 100);
    });
  }
}, BTN, { edge: "falling", repeat: true, debounce: 50 });
```

Use code with caution.

Are you trying to program a **Puck.js smart button** to control a PC emulator, or are you mapping out a specific **creative/interactive media project** based on Leeuwerink's work? Let me know what you are building so we can refine the code or the concept!

### Source links

- [support.google.com](https://support.google.com/knowledgepanel/answer/9787176?hl=en)
- [www.facebook.com](https://www.facebook.com/RetroEntertainmentTV/videos/nhl-97/1420945736085126/)
- [Puck.js device](https://www.puck-js.com/)
- [www.youtube.com](https://www.youtube.com/watch?v=Pn9BNrxe_ek)
- [Jorn Leeuwerink](https://www.aapje.net/)
- [www.filmfestival.nl](https://www.filmfestival.nl/persoon/jorn-leeuwerink)
- [www.cartoonbrew.com](https://www.cartoonbrew.com/cartoon-brew-pick/jorn-leeuwerink-short-film-pig-229452.html)
- [www.facebook.com](https://www.facebook.com/61559045412428/videos/5-euro-op-je-muil-gauw-klassiekers-mag-ik-5-euro-lenen-op-je-muil-gauw-in-deze-l/1325127108559338/)
