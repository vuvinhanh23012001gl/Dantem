export async function postData(url = "", data = {}) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  const text = await response.text();

  let json;
  try {
    json = JSON.parse(text);
  } catch {
    console.error("❌ Response không phải JSON:", text);
    return null;
  }

  if (!response.ok) {
    console.error("❌ HTTP error:", response.status, json);
    return null;
  }

  return json;
}

export async function fetchGet(url, timeout = 10000) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(url, {
            method: "GET",
            headers: {
                "Accept": "application/json",
                "Cache-Control": "no-cache"
            },
            cache: "no-store",
            signal: controller.signal
        });

        clearTimeout(timer);

        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }

        return await response.json();

    } catch (error) {
        console.error("Fetch GET error:", error);
        return null;
    }
}

export const getData = fetchGet;

export async function fetchGetSendData(url, data = {}) {
    try {
        // Chuyển object data thành query string: {id:1,name:"A"} => ?id=1&name=A
        const queryString = new URLSearchParams(data).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;

        const response = await fetch(fullUrl, {
            method: "GET",
            headers: {
                "Accept": "application/json",
                "Cache-Control": "no-cache"
            },
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Fetch GET error:", error);
        return null;
    }
}

