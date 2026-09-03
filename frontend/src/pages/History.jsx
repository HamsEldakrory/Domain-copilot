import { Container, ListGroup } from "react-bootstrap";

import { useClaims } from "../hooks/useClaims";

export default function History() {
  const { data: claims } = useClaims();

  const decided = claims?.filter((claim) => claim.status === "decided") || [];

  return (
    <Container className="mt-4">
      <h4>History (Decided Claims)</h4>

      <ListGroup>
        {decided.map((claim) => (
          <ListGroup.Item key={claim.id}>
            {claim.claim_date} — {claim.status}
          </ListGroup.Item>
        ))}
      </ListGroup>
    </Container>
  );
}
