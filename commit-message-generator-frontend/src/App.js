import React, { useState } from 'react';
import '../styles/App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const handleCommand = async () => {
    if (!input.trim()) return;

    // Add the user's command to the chat log
    setMessages((prevMessages) => [...prevMessages, { type: 'user', text: input }]);

    try {
      const [command, ...args] = input.split(' ');
      let response = '';

      // Process the command
      if (command === '/generate') {
        const commitType = args[0] || 'feat';
        const customMessage = args.slice(1).join(' ') || '';

        response = await window.api.generateCommitMessage(commitType, customMessage);
        setMessages((prevMessages) => [
          ...prevMessages,
          { type: 'system', text: `Generated Commit Message: ${response}` },
        ]);
      } else if (command === '/setup') {
        response = 'Configuration setup started...';
        // (Further setup actions can be added here)
        setMessages((prevMessages) => [...prevMessages, { type: 'system', text: response }]);
      } else {
        response = `Unknown command: ${command}`;
        setMessages((prevMessages) => [...prevMessages, { type: 'error', text: response }]);
      }
    } catch (error) {
      // Handle errors as "enemies" in the chat
      setMessages((prevMessages) => [
        ...prevMessages,
        { type: 'error', text: `Error encountered: ${error.message}` },
      ]);
    }

    setInput('');  // Clear the input field
  };

  return (
    <div className="app-container">
      <h1>Commit Message Quest</h1>
      <div className="chat-log">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.type}`}>
            {msg.type === 'error' ? '⚠️ Enemy Encounter: ' : ''}
            {msg.text}
          </div>
        ))}
      </div>
      <input
        type="text"
        placeholder="Type a command (e.g., /generate feat Add a new feature)"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleCommand()}
        className="command-input"
      />
    </div>
  );
}

export default App;
