const https = require('https');
const querystring = require('querystring');

async function askModel(question, fileId = null) {
  const API_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions';
  // 将API_KEY替换为你的实际秘钥
  const apiKey = 'sk-f4f4de7b9a3f4dbcbab21012757d4fca';
  const systemMessages = [
    { role: "system", content: "You are a helpful assistant." },
    ...(fileId ? [{ role: "system", content: `fileid://${fileId}` }] : [])
  ];

  const postData = JSON.stringify({
    model: "qwen-long",
    messages: [
      ...systemMessages,
      { role: "user", content: question }
    ],
    stream: true
  });

  const options = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`
    }
  };

  return new Promise((resolve, reject) => {
    const req = https.request(API_URL, options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          if (res.statusCode !== 200) {
            reject(new Error(`API request failed with status ${res.statusCode}`));
          } else {
            resolve(response.choices && response.choices[0].message.content || 'Response structure unexpected');
          }
        } catch (parseError) {
          reject(new Error('Failed to parse response as JSON.'));
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.write(postData);
    req.end();
  });
}

const question = "“特殊”新增专项债 特殊在哪里"; // 你的提问
const fileId = "file-fe-1LuMGonfgr3qgC48dm40uBCU";      // 文件ID (可选)

let dataType = "markdown"; // Adjust according to your content type
let data;
let parentID = thisBlock.id;
askModel(question, fileId)
  .then((modelAnswer) => { // Renaming the resolved value for clarity
    // Assigning the model's response to the `data` variable
    data = modelAnswer;

    // Assuming 'dataType' and 'parentID' are correctly defined in your context
    // If 'thisBlock.id' is meant to be used here, ensure it's accessible in this scope
    api.appendBlock(dataType, data, parentID)
      .then(() => {
        // Optionally handle success, e.g., logging
        console.log("Block appended successfully");
      })
      .catch((appendError) => {
        // Handle error while appending the block
        console.error("Failed to append block:", appendError);
      });
  })
  .catch((error) => {
    // Handle the error when asking the model
    console.error("Failed to get model's response:", error);
  });