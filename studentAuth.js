"use strict";

const crypto = require("node:crypto");

const TOKEN_URL = "https://iras.iub.edu.bd:8079/v3/account/token";
const AES_KEY = Buffer.from("rW7aT6RZoP3hjtz0", "utf8");
const AES_IV = Buffer.from("V3k6oMP7C8Jt3E4z", "utf8");

function encryptPassword(password) {
  const cipher = crypto.createCipheriv("aes-128-cbc", AES_KEY, AES_IV);
  // Node's cipher uses PKCS#7 padding by default.
  return Buffer.concat([
    cipher.update(Buffer.from(password, "utf8")),
    cipher.final(),
  ]).toString("base64");
}

async function getToken(studentId, password) {
  const response = await fetch(TOKEN_URL, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      Origin: "https://irasv1.iub.edu.bd",
      Referer: "https://irasv1.iub.edu.bd/",
      "User-Agent": "Mozilla/5.0",
    },
    body: JSON.stringify({
      email: studentId,
      password: encryptPassword(password),
    }),
  });

  const result = await response.json();
  if (!response.ok) {
    throw new Error(
      `IRAS rejected the request (${response.status}): ${JSON.stringify(result)}`,
    );
  }
  if (result.message === "EPF") {
    throw new Error("Invalid student ID or password.");
  }

  const tokenData = Array.isArray(result.data) ? result.data[0] : result;
  const token = tokenData?.access_token;
  if (typeof token !== "string" || token.length === 0) {
    throw new Error(`IRAS returned no access token: ${JSON.stringify(result)}`);
  }
  return {
    access_token: token,
    expires: tokenData.expires,
  };
}

module.exports = { encryptPassword, getToken };
