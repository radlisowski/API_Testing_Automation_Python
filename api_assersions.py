def assert_user_attributes(expected_user, actual_user):
	""" Compare the top-level attributes of two user objects to ensure they match.
	Parameters:
		- expected_user: An object that represents the expected user data. This is the user data you expect to
		retrieve or check against.
		- actual_user: An object containing the actual user data obtained from a source like a server response or database.
	Assertions:
		- Verifies that both user objects have matching usernames.
		- Verifies that both user objects have matching roles.
		- Verifies that both user objects have matching email addresses.
		- Ensures that the 'user_id' in actual_user is not None, indicating it has been properly set. """
	assert expected_user.username == actual_user.username, "Usernames do not match."
	assert expected_user.role == actual_user.role, "Role do not match."
	assert expected_user.email == actual_user.email, "Emails do not match."
	assert actual_user.user_id is not None


def assert_user_addresses(expected_user, actual_user):
	""" Compare the address details of two user objects to ensure they match.
	Parameters:
		- expected_user: An object that represents the expected user data, including addresses.
		- actual_user: An object containing the actual user data obtained from a source like a server response or database.
	Assertions:
		- Checks that both user objects have the same number of addresses.
		- Iterates over each address and checks that street, city, and country are identical.
		- For each address, ensures that the number of phone numbers matches.
		- For each phone number, verifies that both the type and number are identical. """
	assert len(expected_user.addresses) == len(actual_user.addresses), "Number of addresses do not match."
	for index, (original_address, actual_address) in enumerate(zip(expected_user.addresses, actual_user.addresses)):
		assert original_address.street == actual_address.street, f"Streets do not match at index {index}."
		assert original_address.city == actual_address.city, f"Cities do not match at index {index}."
		assert original_address.country == actual_address.country, f"Countries do not match at index {index}."

		assert len(original_address.phone_numbers) == len(actual_address.phone_numbers), f"Number of phone numbers do not match at index {index}."

		for phone_index, (original_phone, actual_phone) in enumerate(zip(original_address.phone_numbers, actual_address.phone_numbers)):
			assert original_phone.type == actual_phone.type, f"Phone types do not match at phone index {phone_index}."
			assert original_phone.number == actual_phone.number, f"Phone numbers do not match at phone index {phone_index}."
