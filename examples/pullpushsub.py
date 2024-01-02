import json
import sys
import requests
from taxii2client.v21 import Server
from taxii2client.exceptions import AccessError
from uuid import uuid4
from time import sleep

# Define your TAXII server and collection details
OPENTAXII_URL = "http://localhost:9000/"
TAXII2_SERVER = OPENTAXII_URL + "taxii2/"
USERNAME = "user_write"
PASSWORD = "user_write"


def pull_data(api_root_url, collection):
    # Pull data from the TAXII collection
    try:
        # Pull data from the collection
        data = collection.get_objects()
        print(f"Num objects pulled: {len(data.get('objects', []))}")
    except AccessError:
        print("[Pull Error] The user does not have write access")
        return None

    return data


def push_data(api_root_url, collection):
    # load stix data and push it
    with open("stix/nettool.stix.json", "r") as f:
        stix_loaded = json.load(f)

    stix_type = stix_loaded["type"]
    stix_id = stix_type + "--" + str(uuid4())
    stix_loaded["id"] = stix_id

    envelope_data = {
        "more": False,
        "objects": [stix_loaded],
    }
    try:
        # Push data to the collection
        collection.add_objects(envelope_data)
        print("Data pushed successfully.")
    except AccessError:
        print("[Push Error] The user does not have write access")


def subscribe(api_root_url, collection):
    total_objects_pulled = 0
    added_after = None

    # Get Authentication Token
    response = requests.post(
        OPENTAXII_URL + "management/auth",
        headers={
            "Content-Type": "application/json",
        },
        json={
            "username": USERNAME,
            "password": PASSWORD,
        },
    )
    auth_token = response.json().get("token", None)

    while True:
        if added_after is None:
            url = api_root_url + "collections/" + collection.id + "/objects/"
        else:
            url = (
                api_root_url
                + "collections/"
                + collection.id
                + f"/objects/?added_after={added_after}"
            )

        # Get all objects from added_after
        response = requests.get(
            url=url,
            headers={
                "Authorization": f"Bearer {auth_token}",
            },
        )
        taxii_env = response.json()
        objects = taxii_env.get("objects", [])

        print(f"Read {len(objects)} objects from the TAXII2 server")
        if len(objects) > 0:
            added_after = response.headers.get("X-TAXII-Date-Added-Last", "")

        sleep(3)


def not_an_action(collection):
    print("That is not an option!")


def main():
    server = Server(
        TAXII2_SERVER,
        user=USERNAME,
        password=PASSWORD,
    )
    print(server.title)
    print("=" * len(server.title))

    print("Select an API Root:")
    print(server.api_roots)
    print()
    for index, aroot in enumerate(server.api_roots, start=1):
        print(f"{index}.")
        try:
            print(f"Title: {aroot.title}")
            print(f"Description: {aroot.description}")
            print(f"Versions: {aroot.versions}")
        except Exception:
            print(
                "This API Root is not public.\nYou need to identify to see this API Root"
            )
        print()

    aroot_choice = input("Enter the number of your choice: ")
    try:
        aroot_choice = int(aroot_choice)
        selected_api_root = server.api_roots[aroot_choice - 1]
        collections_l = selected_api_root.collections
    except (ValueError, IndexError):
        print("Invalid choice. Please enter a valid number.")
        sys.exit()
    except Exception as e:
        print(e)
        print("You cannot access this API Root. You need to authenticate.")
        sys.exit()

    for index, coll in enumerate(collections_l, start=1):
        print(f"{index}.")
        print(f"\tId: {coll.id}")
        print(f"\tTitle: {coll.title}")
        print(f"\tAlias: {coll.alias}")
        print(f"\tDescription: {coll.description}")
        print(f"\tMedia Types: {coll.media_types}")
        print(f"\tCan Read: {coll.can_read}")
        print(f"\tCan Write: {coll.can_write}")
        print(f"\tObjects URL: {coll.objects_url}")
        print(f"\tCustom Properties: {coll.custom_properties}")
        print()

    coll_choice = input("Enter the number of your choice: ")
    try:
        coll_choice = int(coll_choice)
        selected_collection = selected_api_root.collections[coll_choice - 1]
    except (ValueError, IndexError):
        print("Invalid choice. Please enter a valid number.")
        sys.exit()

    actions_d = {
        1: pull_data,
        2: push_data,
        3: subscribe,
    }

    while True:
        print()
        print("1: Pull")
        print("2: Push")
        print("3: Subscribe")
        action_choice = int(input("Enter the number of your choice: "))
        action_func = actions_d.get(action_choice, not_an_action)
        action_func(selected_api_root.url, selected_collection)
        print()


if __name__ == "__main__":
    main()
