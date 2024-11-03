import React, { useState } from 'react';

function Options({ onGenerate }) {
  const [commitType, setCommitType] = useState('feat');
  const [customMessage, setCustomMessage] = useState('');

  const handleGenerate = () => {
    onGenerate(commitType, customMessage);
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

