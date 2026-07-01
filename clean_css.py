import re

with open('src/index.css', 'r') as f:
    css = f.read()

# Remove specific blocks that are no longer needed
blocks_to_remove = [
    r'/\* Página de ejemplo detrás del chat \*/.*?\.tile\s*{[^}]*}',
    r'/\* Widget flotante \*/.*?(?=\.chat-header)',
    r'\.chat-widget\.is-open.*?}',
    r'@media\s*\(max-width:\s*720px\)\s*{[\s\S]*?(?=\.chat-window\.is-fullscreen)',
    r'@media\s*\(max-width:\s*420px\)\s*{[\s\S]*?}',
    r'/\* Pantalla completa para el chat \*/[\s\S]*'
]

for block in blocks_to_remove:
    css = re.sub(block, '', css, flags=re.DOTALL)

# Add the new iframe styles
iframe_styles = """
.chat-window-iframe {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  height: 100dvh;
  background: var(--surface);
  overflow: hidden;
  margin: 0;
  padding: 0;
  font-family: Inter, "Segoe UI", Roboto, Arial, sans-serif;
}

@media (min-width: 768px) {
  .chat-window-iframe {
    display: grid;
    grid-template-columns: 1fr 1.2fr;
    grid-template-rows: auto 1fr auto;
    grid-template-areas:
      "avatar header"
      "avatar messages"
      "avatar input";
  }

  .chat-window-iframe .chat-header {
    grid-area: header;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  }

  .chat-window-iframe .bot-profile {
    grid-area: avatar;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 40px;
    background: linear-gradient(135deg, #0b1a0d 0%, #16361d 100%);
    color: white;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
    border-bottom: none;
    height: 100%;
  }

  .chat-window-iframe .bot-profile .avatar {
    width: min(280px, 45vh);
    height: min(280px, 45vh);
    border-radius: 36px;
    margin-bottom: 28px;
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.4);
    border: 4px solid rgba(53, 153, 70, 0.6);
    background: #000;
  }

  .chat-window-iframe .bot-profile .avatar-media {
    border-radius: 32px;
  }

  .chat-window-iframe .bot-profile .profile-copy {
    text-align: center;
  }

  .chat-window-iframe .bot-profile .profile-copy strong {
    color: #ffffff;
    font-size: 1.6rem;
    margin-bottom: 10px;
  }

  .chat-window-iframe .bot-profile .profile-copy span {
    color: rgba(255, 255, 255, 0.7);
    font-size: 1rem;
    max-width: 320px;
    margin: 0 auto;
  }

  .chat-window-iframe .messages {
    grid-area: messages;
    border-left: 1px solid var(--line);
  }

  .chat-window-iframe .chat-input-area {
    grid-area: input;
    border-left: 1px solid var(--line);
  }
}

@media (max-width: 767px) {
  .chat-window-iframe {
    display: flex;
    flex-direction: column;
  }

  .chat-window-iframe .bot-profile {
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 24px 20px;
    background: linear-gradient(180deg, #eff6f0 0%, #ffffff 100%);
  }

  .chat-window-iframe .bot-profile .avatar {
    width: 140px;
    height: 140px;
    margin-bottom: 12px;
    border-radius: 28px;
    box-shadow: 0 12px 28px rgba(33, 102, 48, 0.2);
    border: 3px solid rgba(53, 153, 70, 0.5);
  }

  .chat-window-iframe .bot-profile .avatar-media {
    border-radius: 24px;
  }

  .chat-window-iframe .bot-profile .profile-copy strong {
    font-size: 1.2rem;
  }

  .chat-window-iframe .bot-profile .profile-copy span {
    font-size: 0.9rem;
  }
  
  .chat-window-iframe .messages {
    flex: 1;
  }
  
  .chat-window-iframe .chat-header {
    border-radius: 0;
  }
}

html, body, #root {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
}
"""

css += iframe_styles

with open('src/index.css', 'w') as f:
    f.write(css)

print("CSS cleaned successfully!")
