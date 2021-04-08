# HackerNews-sentiment-analysis

I chose to use Python as it is a perfect fit for scripting purposes. 
I also read in the Serverless tutorials that it is a good fit for it.
I've used the pytho 'requests' library for the initial http request for top stories. For
all other requests, which are performed asynchronously, I've chosen to use aiohttp, a library
which enables asynchronous requests through asyncio (which was also utilised.
The sentiment analysis itself was performed via AWS comprehend. I chose it because it seemed, from
my initial research, to be used rather commonly with Serverless Framework and Python through 
AWS Lambda.