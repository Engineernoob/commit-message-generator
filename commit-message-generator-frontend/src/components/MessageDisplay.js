import React from 'react';

function MessageDisplay({ message }) {
  return (
    <div>
      <h2>Generated Commit Message:</h2>
      <p>{message || 'No message generated yet.'}</p>
    </div>
  );
}

export default MessageDisplay;
