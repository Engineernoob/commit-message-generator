import React, { useState } from 'react';

function Options({ onGenerate }) {
  const [commitType, setCommitType] = useState('feat');
  const [customMessage, setCustomMessage] = useState('');

  const handleGenerate = async () => {
    try {
      // Call the backend function exposed in preload.js
      const generatedMessage = await window.api.generateCommitMessage(commitType, customMessage);
      onGenerate(generatedMessage);
    } catch (error) {
      console.error("Error generating commit message:", error);
    }
  };

  return (
    <div className="options">
      <label>
        Commit Type:
        <select value={commitType} onChange={(e) => setCommitType(e.target.value)}>
          <option value="feat">Feature</option>
          <option value="fix">Fix</option>
          <option value="chore">Chore</option>
        </select>
      </label>
      <input
        type="text"
        placeholder="Enter custom message"
        value={customMessage}
        onChange={(e) => setCustomMessage(e.target.value)}
      />
      <button onClick={handleGenerate}>Generate Commit Message</button>
    </div>
  );
}

export default Options;
