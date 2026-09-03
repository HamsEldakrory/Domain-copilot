import { Link } from "react-router-dom";
import { Container, Table, Spinner, Navbar, Nav } from "react-bootstrap";
import { useClaims } from "../hooks/useClaims";
import { useCurrentUser } from "../hooks/useAuth";
export default function Claims() {
  const { data: claims, isLoading } = useClaims();
  const { data: user } = useCurrentUser(true);
  return (
    <>
      <Navbar bg="light" className="mb-4 px-3">
        <Navbar.Brand>Domain Copilot</Navbar.Brand>

        <Nav className="ms-auto">
          <Nav.Link as={Link} to="/claims">
            Claims
          </Nav.Link>

          <Nav.Link as={Link} to="/history">
            History
          </Nav.Link>

          {user?.role === "MANAGER" && (
            <Nav.Link as={Link} to="/policies/upload">
              Upload Policy
            </Nav.Link>
          )}

          <Navbar.Text className="ms-2">
            {user?.username} ({user?.role})
          </Navbar.Text>
        </Nav>
      </Navbar>

      <Container>
        <h4>Claims</h4>
        {isLoading ? (
          <Spinner />
        ) : (
          <Table striped bordered hover>
            <thead>
              <tr>
                <th>Claim Date</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>

            <tbody>
              {claims?.map((claim) => (
                <tr key={claim.id}>
                  <td>{claim.claim_date}</td>

                  <td>{claim.status}</td>

                  <td>
                    <Link to={`/claims/${claim.id}`}>Open</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Container>
    </>
  );
}
