export default async function handler(req, res) {
  // Only allow POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // FAL_KEY must be set in Vercel Environment Variables
  const FAL_KEY = process.env.FAL_KEY;
  if (!FAL_KEY) {
    return res.status(500).json({ error: 'FAL_KEY environment variable not configured on server.' });
  }

  const { prompt, model, image_size, num_inference_steps } = req.body;

  if (!prompt || !model) {
    return res.status(400).json({ error: 'Missing required fields: prompt, model' });
  }

  try {
    const falResponse = await fetch(`https://fal.run/${model}`, {
      method: 'POST',
      headers: {
        'Authorization': `Key ${FAL_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt,
        image_size: image_size || 'square_hd',
        num_inference_steps: num_inference_steps || 4,
        num_images: 1,
        enable_safety_checker: true,
      }),
    });

    const data = await falResponse.json();

    if (!falResponse.ok) {
      return res.status(falResponse.status).json({
        error: data.detail || data.message || 'FAL API error',
      });
    }

    return res.status(200).json(data);
  } catch (err) {
    return res.status(500).json({ error: 'Server error: ' + err.message });
  }
}
