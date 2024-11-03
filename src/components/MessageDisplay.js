import React from 'react';

function MessageDisplay({ message }) {
  return (
    <div className="message-display">
      <h2>Generated Commit Message:</h2>
      <p>{message || 'No message generated yet.'}</p>
    </div>
  );
}

export default MessageDisplay;
