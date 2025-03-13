# aitp-agent

### This agent communicate to an API using AITP (Agent Interaction and Transaction Protocol).
The AITP protocol is a standardized format for an API to serve its tools to AI agents.
Here is a example of how the protocol should be implemented in the API:


#
#### Protocol Discovery
The api implementation must expose the AITP config in a endpoint with the following structure:

#### Base Structure
```typescript
{
  name: string,
  description: string,
  api_commands: APICommand[]
}
```

#### API Command Structure
Each command in the api_commands array must follow this format:
```typescript
{
  command: string,
  method: "GET" | "POST",
  endpoint: string,
  description: string,
  prompt: string,
  parameters: {
    name: string,
    type: string,
    description: string,
    required: boolean
  }[],
  paymentRequired?: boolean,
  inputSchema?: {
    url: string,
    prompt: string
  },
  outputSchema?: {
    url: string,
    prompt: string
  }
}
```

