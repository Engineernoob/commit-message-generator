import React, { useState } from 'react';
import { TextField, Button, Typography, Paper, Box, Stack, Card, CardContent } from '@mui/material';
import ErrorIcon from '@mui/icons-material/Error';
import PersonIcon from '@mui/icons-material/Person';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

const BACKEND_URL = 'http://localhost:5000'; // Update this to match your backend's URL

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const handleCommand = async () => {
    if (!input.trim()) return;

    setMessages((prevMessages) => [...prevMessages, { type: 'user', text: input }]);

    try {
      const [command, ...args] = input.split(' ');
      let response = '';

      if (command === '/generate') {
        const commitType = args[0] || 'feat';
        const customMessage = args.slice(1).join(' ') || '';

        // Send a POST request to the Flask backend
        const res = await fetch(`${BACKEND_URL}/generateCommitMessage`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ commitType, customMessage }),
        });

        if (res.ok) {
          const data = await res.json();
          response = `Generated Commit Message: ${data.commitMessage}`;
        } else {
          response = 'Error generating commit message.';
        }
      } else if (command === '/help') {
        response = "Commands: /generate [type] [message], /help";
      } else {
        response = `Unknown command: ${command}`;
      }

      setMessages((prevMessages) => [
        ...prevMessages,
        { type: command === '/help' || command === '/generate' ? 'system' : 'error', text: response },
      ]);
    } catch (error) {
      setMessages((prevMessages) => [
        ...prevMessages,
        { type: 'error', text: `Error encountered: ${error.message}` },
      ]);
    }

    setInput('');
  };

  const getMessageIcon = (type) => {
    if (type === 'error') return <ErrorIcon color="error" />;
    if (type === 'system') return <CheckCircleIcon color="success" />;
    return <PersonIcon color="primary" />;
  };

  const getMessageColor = (type) => {
    if (type === 'error') return '#ffcccc';
    if (type === 'system') return '#ccffcc';
    return '#cce5ff';
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Commit Message Quest
      </Typography>

      <Paper
        variant="outlined"
        sx={{
          width: '100%',
          maxWidth: 500,
          height: 400,
          overflowY: 'auto',
          padding: 2,
          marginBottom: 2,
          backgroundColor: '#333',
        }}
      >
        <Stack spacing={2}>
          {messages.map((msg, index) => (
            <Card
              key={index}
              variant="outlined"
              sx={{
                backgroundColor: getMessageColor(msg.type),
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <CardContent sx={{ display: 'flex', alignItems: 'center', padding: 1 }}>
                <Box sx={{ marginRight: 1 }}>{getMessageIcon(msg.type)}</Box>
                <Typography sx={{ color: '#333' }}>{msg.text}</Typography>
              </CardContent>
            </Card>
          ))}
        </Stack>
      </Paper>

      <TextField
        label="Type a command"
        placeholder="e.g., /generate feat Add a new feature"
        variant="outlined"
        fullWidth
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleCommand()}
        sx={{ maxWidth: 500, marginBottom: 2 }}
      />
      
      <Button
        variant="contained"
        color="primary"
        onClick={handleCommand}
        sx={{ maxWidth: 500 }}
      >
        Execute Command
      </Button>
    </Box>
  );
}

export default App;
