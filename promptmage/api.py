"""This module contains the API for the PromptMage package."""

import inspect
import pkg_resources
from pathlib import Path

from fastapi import FastAPI, Path, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware


from promptmage import PromptMage


class PromptMageAPI:

    def __init__(self, mage: PromptMage):
        self.mage = mage

    def get_app(self) -> FastAPI:
        """Create a FastAPI application to serve the PromptMage instance."""
        app = FastAPI(
            title=f"PromptMage API: {self.mage.name}", description="API for PromptMage."
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # create index endpoint
        # @app.get("/")
        # async def index():
        #    return HTMLResponse("<h1>Welcome to the FlowForge API</h1>")

        # create the endpoints for each step
        step_list = []
        for step_name, func in self.mage.steps.items():
            signature = inspect.signature(func)
            path = f"/api/{step_name}"
            params = []

            for name, param in signature.parameters.items():
                # ignore prompt parameter
                if name == "prompt":
                    continue
                if param.default is inspect.Parameter.empty:
                    # Assume required parameters are path parameters
                    new_param = inspect.Parameter(
                        name,
                        kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        default=Path(..., description=f"Path parameter `{name}`"),
                        annotation=param.annotation,
                    )
                    path += f"/{{{name}}}"  # Add to the path
                else:
                    # Parameters with defaults are query parameters
                    new_param = inspect.Parameter(
                        name,
                        kind=inspect.Parameter.KEYWORD_ONLY,
                        default=Query(
                            param.default, description=f"Query parameter `{name}`"
                        ),
                        annotation=param.annotation,
                    )
                params.append(new_param)

            # Update the signature for the endpoint function
            new_signature = signature.replace(parameters=params)
            endpoint_func = self.create_endpoint_function(func, new_signature)
            setattr(
                endpoint_func, "__signature__", new_signature
            )  # Update the signature for FastAPI to recognize

            # Add the route to FastAPI
            app.add_api_route(path, endpoint_func, methods=["GET"])
            step_list.append({"name": step_name, "path": path})

        # add a route to list all available steps with their names and input variables
        @app.get("/api/steps")
        async def list_steps():
            return step_list

        static_files_path = pkg_resources.resource_filename("promptmage", "static/")
        app.mount(
            "/static/",
            StaticFiles(directory=static_files_path, html=True),
            name="static",
        )
        return app

    def create_endpoint_function(self, func, params):
        # Define the endpoint function using dynamic parameters
        async def endpoint(*args, **kwargs):
            # Directly pass the keyword arguments to the function
            return func(*args, **kwargs)

        return endpoint