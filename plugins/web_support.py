from aiohttp import web

routes = web.RouteTableDef()

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AdsGram Demo</title>

    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <script src="https://sad.adsgram.ai/js/sad.min.js"></script>
</head>
<body>

    <h2>AdsGram Test</h2>

    <button onclick="showAd()">Watch Ad</button>

    <script>
        const tg = window.Telegram.WebApp;
        tg.expand();

        const AdController = window.Adsgram.init({
            blockId: "38337"
        });

        async function showAd() {
            try {
                const result = await AdController.show();

                console.log(result);

                alert("Reward Granted!");

                // Optional: notify server
                fetch("/reward", {
                    method: "POST"
                });

            } catch (err) {
                console.log(err);
                alert("Ad skipped or failed.");
            }
        }
    </script>

</body>
</html>
"""


@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.Response(
        text=HTML,
        content_type="text/html"
    )


@routes.get("/reward")
async def reward_handler(request):
    user_id = request.query.get("userid")

    if not user_id:
        return web.Response(text="Missing userid")

    # Give reward here
    print(f"Reward claimed by {user_id}")

    return web.Response(
        text="✅ Reward granted!"
    )
async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app
