import React, { useState } from 'react';
import { TextField, Button, Typography, Paper, Box, Stack, Card, CardContent } from '@mui/material';
import ErrorIcon from '@mui/icons-material/Error';
import PersonIcon from '@mui/icons-material/Person';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

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

        // Use the IPC API to generate the commit message
        response = await window.api.generateCommitMessage(commitType, customMessage);
        setMessages((prevMessages) => [
          ...prevMessages,
          { type: 'system', text: `Generated Commit Message: ${response}` },
        ]);
      } else if (command === '/help') {
        response = "Commands: /generate [type] [message], /help";
        setMessages((prevMessages) => [...prevMessages, { type: 'system', text: response }]);
      } else {
        response = `Unknown command: ${command}`;
        setMessages((prevMessages) => [...prevMessages, { type: 'error', text: response }]);
      }
    } catch (error) {
      setMessages((prevMessages) => [
        ...prevMessages,
        { type: 'error', text: `Error encountered: ${error.message}` },
      ]);
    }

    setInput('');  // Clear the input field
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
                <Typography sx={{ color: '#333' }}>
                  {msg.type === 'error' ? '⚠️ ' : ''}{msg.text}
                </Typography>
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
